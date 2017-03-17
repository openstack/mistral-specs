..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================
Workflow Advanced publishing
============================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-advanced-publishing

Advanced publishing will eliminate confusions around current workflow
publishing mechanism, unify publishing for all clauses 'on-success',
'on-error' and 'on-complete' and define publishing of variable scopes into
different scopes: branch, global, global atomic.
The proposed workflow language syntax will also be extensible if such a need
occurs in the future.


Problem description
===================

Currently 'publish' keyword in Mistral saves variables into a storage
(context) which is associated only with a branch.

Example:

 ::

   ---
   version: '2.0'

   wf:
     tasks:
       A:
         action: std.noop
         publish:
           my_var: 1
         on-success: A1

       A1:
         action: my_action param1=<% $.my_var %>

       B:
         action: std.noop
         publish:
           my_var: 2
         on-success: B1

       B1:
         action: my_action param1=<% $.my_var %>


The expression "$.my_var" in the declaration of A1 will always evaluate to 1,
for B1 it will always evaluate to 2. This doesn't depend on the order in which
A and B will run. This is because we have two branches (A -> A1 and B -> B1)
for which the variable "my_var" has its own different version.

Sometimes though we need to be able to share data across branches which is now
impossible due to aforementioned semantics.
The concept of workflow global context can help solve this problem. The word
"global" here means "accessible from any workflow branch".

We also need an ability to make atomic updates of global workflow context.
It's necessary when we, for example, want to create a global counter (e.g.
counter of network calls to external systems performed by a workflow).

Currently, we also have the keyword 'publish-on-error' that works the same way
as 'publish' but in case of an error of task action (or workflow).

If we take the path of adding new keywords for all these cases we'd come up
with the following keywords:

* 'publish' - for branch publishing, currently exists
* 'publish-on-error' - for branch publishing in case of error, currently
  exists
* 'publish-global' - for global publishing, doesn't exist
* 'publish-global-atomic' - for global atomic publishing, doesn't exist
* 'publish-global-on-error' - for global publishing in case of error, doesn't
 exist
* 'publish-global-atomic-on-error' - for global atomic publishing in case of
 error, doesn't exist

So, we see that a number of keywords is growing and so does the length of the
keywords. This all leads to a non-concise messy syntax.
This approach is also not extensible because every time we'd like to add a new
scope we'll have to add two new keywords (one for 'on-success' and one for
'on-error').

Use Cases
---------

* Building conditions based on events happened in parallel workflow branches.
  Example: one branch needs to notify the other one that it should stop.
* Passing data between branches. Example: one branch needs to wait till the
  other one produces some expected result. This is, essentially, creating
  a cross-branch mutex.
* Counters that need to decrement or increment atomically.

Proposed change
===============

In order to achieve this goal the proposal is:

* Extend semantics of existing 'on-success', 'on-error' and 'on-complete'
  keywords so that along with next tasks they can also have a description of
  publishing into different scopes. Now 'on-success', 'on-error' and
  'on-complete' can be either a string, a list of strings or a list of
  dictionaries. In order to include publishing they should be dictionaries
  with two keys 'publish' and 'next'. See the detailed example below.
* 'publish' defined under 'on-success', 'on-error' and 'on-complete' can
  optionally define scopes (but at least one) to be able to publish into
  different scopes: 'branch', 'global' and 'atomic' for global atomic
  publishing. An alternative for 'atomic' could be 'global-atomic' but just
  'atomic' seems to be sufficient because atomic publishing for a branch is
  pointless. Specifying variables under 'branch' will make Mistral publish
  into a branch workflow context just like 'publish' and 'publish-on-error'
  currently do. Specifying variables under 'global' will make Mistral publish
  into a global workflow context. It's important to note that this is an
  unprotected way of modifying data because race conditions are possible when
  writing different values for same variables in the global context from
  parallel branches. In other words, if we have branches A and B and there are
  tasks in these branches that first read global variable X, then increment it
  and write the new value Mistral won't provide any guarantee that the result
  value after finishing tasks A and B will be X + 2. In some cases it can be
  X + 1 because the following may happen: task A read X, Task B read X, Task B
  incremented X, Task B wrote X + 1, Task A incremented X (the old one, not
  incremented by B), Task A wrote X + 1.
  'atomic' scope can address the aforementioned problem by providing a
  guarantee that after task A read a global variable X no other task can read
  variable X until a transaction processing task A is committed.
* If 'publish' is defined in 'on-complete' and also in 'on-success' and/or
  'on-error' then the result of publishing will be a merge of what
  'on-complete' publishes with what 'on-success' or 'on-error' publishes
  depending on the task status. If 'on-complete' publishes variables that are
  also published by 'on-success' or 'on-error' then latter take precedence.
  In other words, 'on-complete' in this case is considered a default which
  can be overridden by more specific 'on-XXX' clause.
* The keyword 'next' defined under 'on-success'/'on-error'/'on-complete'
  becomes optional since the only purpose of 'on-xxx' clause may be publishing.
* Currently existing 'publish' and 'publish-on-error' will still be available
  with the same semantics and may be deprecated in the future versions of the
  language.
* Add the new YAQL/Jinja function "global()" to explicitly access
  variables in workflow global context.
* Make global variables also accessible using "$." in YAQL and "_." in
  Jinja in a way that branch variables can shadow them if they are
  published in the current branch.

Another positive effect of this change would be defining of what should happen
in case of success or error at the same place: both publishing and scheduling
next tasks.

Example #1 (writing and reading global variables):

 ::

   ---
   version: '2.0'

   wf:
     tasks:
       A:
         action: std.noop
         on-success:
           publish:
             branch:
               my_var: "branch value"
             global:
               my_var: "global value"
           next: A1

       A1:
         # $.my_var will always evaluate to "branch value" because A1 belongs
         # to the same branch as A and runs after A. When using "$" to access
         # context variables branch values have higher priority.
         # In order to access global context reliably we need to use YAQL/Jinja
         # function 'global'. So global(my_var) will always evaluate to
         # 'global value'.
         action: my_action1 param1=<% $.my_var %> param2=<% global(my_var) %>

       B:
         # $.my_var will evaluate to "global value" if task A completes
         # before task B and "null", if not. It's because A and B are
         # parallel and 'publish' in A doesn't apply to B, only
         # 'publish-global' does. In this example global(my_var) has the same
         # meaning as $.my_var because there's no ambiguity from what context
         # we should take variable 'my_var'.
         action: my_action2 param1=<% $.my_var %> param2=<% global(my_var) %>


Example #2 (writing global variables atomically):

 ::

   ---
   version: '2.0'

   wf:
     vars:
       - counter: 0

     output:
       counter: <% $.counter %>

     tasks:
       task1:
         action: std.noop
         on-success:
           publish:
             atomic:
               counter: <% global(counter) + 1 %>

       task2:
         action: std.noop
           on-success:
             publish:
               atomic:
                 counter: <% global(counter) + 1 %>


After running this workflow its output must always be 2.

Alternatives
------------

None.

Data model impact
-----------------

Workflow execution object already has the field "context" which is now
immutable and initialized with openstack specific data, execution id and
environment variables. In order to get the full context for evaluating a
YAQL/Jinja expression in a task declaration we always build a context view
merged from workflow input, workflow execution "context" field and branch
specific context (e.g. task inbound context when evaluating action
parameters). The field "context" can play the role of workflow global
context. However, the idea to reuse this field can be revisited during
the implementation phase.

REST API impact
---------------

None.

End user impact
---------------

New workflow language feature that explicitly allows to define scopes(contexts)
of published variables.

Performance Impact
------------------

When using the scope "atomic" we'll need to use locking in order to prevent
concurrent modifications of global workflow context while reading and modifying
it at publishing stage of a certain task. In fact, this is equal to locking the
whole workflow execution object and hence will have a significant performance
impact in case of many parallel tasks. For this reason, "atomic" needs to be
well documented and used with precaution.

Deployer impact
---------------

None.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  rakhmerov

Other contributors:
  melisha

Work Items
----------

* Change 'on-success', 'on-error' and 'on-complete' in the specification of
  direct workflow task in the way described above.
* Make changes in Mistral engine to publish variables into global context
  (preliminarily it will be the field 'context' of workflow execution object).
* Implement YAQL/Jinja function 'global' to explicitly read variables from
  workflow global context.
* Add locking of workflow global context (i.e. workflow execution) in case of
  using 'atomic' scope. A thread that acquires a lock must first refresh state
  of workflow execution and then proceed with publishing etc.

Dependencies
============

None.


Testing
=======

* Unit tests for publishing into all scopes and using 'global' function for
  different cases: parallel tasks, sequential tasks.
* Unit tests to check that branch-local variables take precedence when
  reading variables using '$.' in YAQL and '_.' in Jinja.
* Unit tests for 'atomic' scope that checks atomicity of reads and writes of
  global variables. Although unit tests can't fully test this feature. In order
  to fully test it we need to have a test with multiple Mistral engines to make
  sure we have concurrent access to workflow execution.

References
==========

None.
