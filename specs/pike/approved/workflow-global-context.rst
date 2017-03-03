..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=======================
Workflow Global Context
=======================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-global-wf-context

Workflow global context will allow to store variables not associated with
particular workflow branches.

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

* Add the new keyword "publish-global" which is similar to "publish"
  with the difference that it publishes variables into workflow global
  context instead of branch workflow context. It's important to note
  that this is an unprotected way of modifying data because race
  conditions are possible when writing different values for same
  variables in the global context from parallel branches. In other
  words, if we have branches A and B and there are tasks in these
  branches writing different values to the variable X in the global
  context Mistral won't provide any guarantees as far as what value
  is going to be assigned to X and what value will be lost. Users need
  to understand possible consequences.
  For instance, using this keyword it's impossible to create an atomic
  counter since it doesn't assume acquiring a lock under which we can
  safely perform multiple operations (e.g. read and then write).
  However, for many scenarios even this model can be useful. For example,
  if there's only one branch writing values and others are only readers.
* Add the new YAQL/Jinja function "global()" to explicitly access
  variables in workflow global context.
* Make global variables also accessible using "$." in YAQL and "_." in
  Jinja in a way that branch variables can shadow them if they are
  published in the current branch.
* Add the new keyword "publish-global-atomic" which is similar to
  "publish-global" but allows to atomically read and write variables
  in workflow global context by acquiring a temporary lock on it.
  Unlike 'publish-global' this will allow to create atomic counters
  when we need to perform multiple operations against the storage
  atomically.

Example #1 (writing and reading global variables):

 ::

   ---
   version: '2.0'

   wf:
     tasks:
       A:
         action: std.noop
         publish:
           my_var: "branch value"
         publish-global:
           my_var: "global value"
         on-success: A1

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

   vars:
     - my_global_var: 0

   wf:
     tasks:
       task1:
         action: std.noop
         publish-global-atomic:
           counter: <% global(my_global_var) + 1 %>

       task2:
         action: std.noop
         publish-global-atomic:
           counter: <% global(my_global_var) + 1 %>


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

New workflow language feature that allows to store global variables into
workflow context.

Performance Impact
------------------

When using "publish-global-atomic" we'll need to use locking in order
to prevent concurrent modifications of global workflow context while
reading and modifying it when processing a certain task. In fact, this is
equal to locking the whole execution object and hence will have a serious
performance impact in case of many parallel tasks. For this reason,
"publish-global-atomic" needs to be well documented and used with
precaution.

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

* Add 'publish-global' and 'publish-global-atomic' into the direct workflow
  specification.
* Make changes in Mistral engine to publish variables into global context
  (preliminarily it will be the field 'context' of workflow execution object).
* Implement YAQL/Jinja function 'global' to explicitly read variables from
  workflow global context.
* Add locking workflow global context (i.e. workflow execution) in case of
  using 'publish-global-atomic'. A thread that acquires a lock must first
  refresh state of workflow execution and then proceed with publishing etc.

Dependencies
============

None.


Testing
=======

* Unit tests for 'publish-global' keyword and 'global' function in different
  cases: parallel branches, sequential branches.
* Unit tests to check that branch-local variables take precedence when
  reading variables using '$.' in YAQL and '_.' in Jinja.
* Unit tests for 'publish-global-atomic' that checks atomicity of reads and
  writes of global variables. Although unit tests can't fully test this
  feature. In order to fully test it we need to have a test with multiple
  Mistral engines to make sure we have concurrent access to workflow execution.

References
==========

None.
