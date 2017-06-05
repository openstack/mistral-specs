..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================================
Create and run workflows within a namespace
===========================================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/create-and-run-workflows-within-a-namespace

Creating and running workflows within a namespace will allow users to create
many workflows with the same name. This is useful when a user already has many
workflows that are connected to each other implemented and one of the workflow
names is already in use and the user does not want to edit that workflow and
all the ones referencing it or merge them to a workbook. This is possible
because the namespace is not a part of the Mistral language.


Problem description
===================

When a workflow name is already in use, it takes editing the workflow the user
wants to add to mistral or delete the existing one.

Use Cases
---------

* When there are many users writing workflows in the same tenant simultaneously
  each can use a different namespace, so there will be no clashes preventing
  any of the users to add the workflow he created to mistral.

* If a workflow definition is not allowed to be modified, but a workflow with
  the same name already exists in Mistral and the user wants to upload the
  workflow and create an execution from it.


Proposed change
===============

Add a new namespace parameter to both workflow definition creation, workflow
definition deletion, workflow execution creation and other relevant APIs.

If a workflow definition creation request has a namespace specified in it, the
workflow name should be unique only within the namespace. If no namespace is
passed, the name should be unique within the group of workflow definitions
without a namespace (will be referred as the default namespace from here on).

If a workflow execution request from the user, has a namespace specified in it,
mistral will search for the workflow definition within the namespace only.
However, if the workflow execution came from the mistral engine (e.g
sub-workflow execution), mistral will first try finding the workflow definition
within the namespace, and only if one does not exist, mistral will try finding
it the default namespace. By default the namespace passes to the sub-workflows
execution. If a workflow definition only exists in another namespace that is
not the default namespace, it will not be found, and the create workflow
execution request will fail.

In the future we might want to add a namespace for actions and workbooks (but
for now workbooks and workflows created from them, are always in the default
namespace).

An example to explain how the namespace moves recursively to sub-workflow
executions.

Given there are 3 workflows in the workflow table. Two workflows definitions
called 'wf' and 'sub_sub_workflow'are in the same namespace - a namespace we
will call 'abc', and one workflow definition called 'sub_workflow' in the
default namespace.

Visualization of a partial workflow definitions table:

  +----+---------------------+-----------+
  | ID | name                | namespace |
  +----+---------------------+-----------+
  | 1  | wf                  | abc       |
  +----+---------------------+-----------+
  | 2  | sub_wf              |           |
  +----+---------------------+-----------+
  | 3  | sub_sub_wf          | abc       |
  +----+---------------------+-----------+
  | 4  | sub_sub_wf          |           |
  +----+---------------------+-----------+

Workflow definition for 'wf' with ID 1:
  .. code-block:: yaml

    ---
    version: '2.0'
    wf:
      tasks:
        t1:
          workflow: sub_wf


Workflow definition for 'sub_wf' with ID 2:
  .. code-block:: yaml

    ---
    version: '2.0'
    sub_wf:
      tasks:
        t2:
          workflow: sub_sub_wf

Workflow definition for 'sub_sub_wf' with ID 3:
  .. code-block:: yaml

    ---
    version: '2.0'
    sub_sub_wf:
      tasks:
        t3:
          action: std.noop

Workflow definition for 'sub_sub_wf' with ID 4:
  .. code-block:: yaml

    ---
    version: '2.0'
    sub_sub_wf:
      tasks:
        should_not_run:
          action: std.fail

As you notice, namespace is not and should never be a part of the language.

By calling the execution of workflow with name 'wf' within namespace 'abc', it
is required for workflow with name 'wf' in namespace 'abc' to run, and when
task t1 is executed to call workflow 'sub_wf' within the default namespace
(since no workflow with name 'sub_wf' exist within namespace 'abc'), but still
remember the namespace is 'abc' so that when task t2 will be executed, the
workflow that will be executed is workflow 'sub_sub_wf' in namespace 'abc' with
ID '3', rather than workflow 'sub_sub_wf' in the default namespace with ID '4'.
The execution described above should result in success.

More strictly speaking, when it comes to calling nested workflows the namespace
of the top most workflow is propagated down to its children. So that when
Mistral needs to resolve a workflow name, it first searches the configured name
in that propagated namespace, and if it doesn't exist there, Mistral will try
to find it in the default namespace.

A workflow execution can only trigger an execution of a workflow within both
the same tenant and namespace or within both the same tenant and the default
namespace.

For workbooks that means that all workflows within the workbook could only call
workflows in the default namespace.

Leading suggestion for the creation API of the 'wf' execution is this:
  .. code-block::

    POST /v2/executions
    {
      "workflow_name": "wf",
      "workflow_namespace": "abc"
    }

Leading suggestion for passing the namespace from execution to sub-execution
recursively is putting it in the params of the execution possible under env.
A user is not allowed to add any key that starts with two underscores to the
env.

Example of how such row might look like in the database:
  .. code-block::

    mysql> select * from workflow_executions_v2 where id='3'\G;
    *************************** 1. row ***************************
              created_at: 2017-06-19 10:59:29
              updated_at: 2017-06-19 10:59:30
                   scope: private
              project_id: 1
                      id: 3
                    name: sub_sub_wf
             description:
           workflow_name: sub_sub_wf
      workflow_namespace: abc
             workflow_id: 3
                    spec: {"tasks": {"t3": {"action": "std.noop", "version": "2.0", "type": "direct", "name": "t3"}}, "name": "sub_sub_wf", "version": "2.0"}
                   state: SUCCESS
              state_info: NULL
                    tags: NULL
         runtime_context: {"index": 0}
                accepted: 1
                   input: {}
                  output: {}
                  params: {"env": {"__namespace": "abc"}}

Notice the last line where under params->env we have a key called '__namespace'

In the example described above, if a user decides to add a workflow with the
name 'sub_wf' to the 'abc' namespace, the next time the workflow will be
executed, the new workflow called 'sub_wf' from the 'abc' namespace will be
triggered by the workflow with the name 'wf' from the 'abc' namespace, instead
of the workflow 'sub_wf' from the default namespace.

Regarding the results of the current APIs see the next examples that all assume
that the workflows described in the next table are the only one that exist.

Table:
  +----+---------------------+-----------+
  | ID | name                | namespace |
  +----+---------------------+-----------+
  | 1  | wf                  | abc       |
  +----+---------------------+-----------+
  | 2  | sub_wf              |           |
  +----+---------------------+-----------+
  | 3  | sub_sub_wf          | abc       |
  +----+---------------------+-----------+
  | 4  | sub_sub_wf          |           |
  +----+---------------------+-----------+
  | 5  | example_wf          | example_1 |
  +----+---------------------+-----------+
  | 6  | example_wf          | example_a |
  +----+---------------------+-----------+

Examples:

  * **GET /v2/workflows**
    Will return all 6 workflows

  * **GET /v2/workflows/wf**
    Will return an error "workflow not found [workflow_identifier=wf]

  * **GET /v2/workflows/sub_wf**
    Will return workflow 'sub_wf' from the default namespace (ID=2).

  * **GET /v2/workflows/sub_sub_wf**
    Will return workflow 'sub_sub_wf' from the default namespace (ID=4).

  * **GET /v2/workflows/example_wf**
    Will return an error "workflow not found [workflow_identifier=example_wf]

  * **DELETE /v2/workflows/wf**
    Will throw an exception, because no namespace supplied and no such workflow
    exist in the default namespace

  * **DELETE /v2/workflows/sub_wf**
    Will delete the workflow with the name 'sub_wf' from the default namespace
    (ID=2).
    This should be allowed in order to let users that don't use namespaces to
    work as they are used to.

  * **DELETE /v2/workflows/sub_sub_wf**
    Will delete the workflow with the name 'sub_sub_wf' from the default
    namespace (ID=4).

  * **DELETE /v2/workflows/example_wf**
    Will return an error "workflow not found [workflow_identifier=example_wf]

  * PUT will have similar results to DELETE


Alternatives
------------

We can try and use workbooks, but the down side is it forces the user to merge
his workflows, and might result in a hugh file, that a user might find to be
hard to edit and read.

For the described namespace design, we can use different names. For example in
the create execution API we can call the new key 'workflow_namespace' instead
of 'namespace'. Also the default namespace currently described is the empty
string (''), but it can be something like "<default-namespace>". We should also
consider saving some namespaces to future system use (for example namespaces
that starts with 2 underscores '__')


Data model impact
-----------------

The proposed change must come with a change to the data model.

For workflow definition, a namespace should be added to the model and the DB
workflow_definitions_v2 table. And the same for workflow execution, plus it
should also be under env in params, so it will seep easily to the sub-workflow
executions. In the case of workflow execution there is also the option of just
adding it to the env under params.

In the future we might create a namespace table. Migration from current
suggested model to one that includes a separate table for namespace, should be
easy using SQLAlchemy.

REST API impact
---------------

Optional namespace parameter will be added to relevant requests:

  * create workflow definition within a namespace::

        POST /v2/workflows?namespace=NAMESPACE
        RAW_WF_DEFINITION

  * delete workflow definition within a namespace::

        DELETE /v2/workflows/WORKFLOW_IDENTIFIER?namespace=NAMESPACE

  * get a workflow definition within a namespace::

        GET /v2/workflows/WORKFLOW_IDENTIFIER?namespace=NAMESPACE

  * get all the workflow definitions within a given namespace::

        GET /v2/workflows?namespace=NAMESPACE

  * update a workflow definition within a given namespace::

        PUT /v2/workflows?namespace=NAMESPACE
        RAW_WF_DEFINITION

  * create an execution of a workflow where the workflow belongs to given::

        POST /v2/executions
        {
          "workflow_name": "WORKFLOW_NAME",
          "workflow_namespace": "NAMESPACE"
        }

  * get a list of all the namespaces::

        GET /v2/namespaces


End user impact
---------------

The new namespace request parameter should be added to the python-mistralclient
as well.

Performance Impact
------------------

None.

Deployer impact
---------------

Database migration should be done when upgrading mistral to a version that
includes this change.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  michal-gershenzon

Other contributors:
  melisha

Work Items
----------

* Adding namespace parameter to create workflow definition, delete workflow
  definition and create workflow execution requests.

* Change the way workflow definition are queried during execution.

* Tests

* Database migration script

* Documentation

* Add new parameter to python-mistralclient


Nice to have work items:

* Adding namespace as a filter parameter of get workflow definition

* Adding namespace as a filter parameter of update workflow definition

* Adding namespace as a filter parameter of get workflow executions

* Supporting the namespace feature with workbooks

* Adding namespaces API endpoint


Dependencies
============

None.


Testing
=======

* Create a workflow under some namespace that already exist in the default
  namespace.

* Create a workflow under the default namespace that calls the workflow above.
  Run it once under the default namespace and once under the namespace from
  previous section and see each time the expected sub-workflow execution is
  created.

* Create a workflow under some namespace that does not exist in the default
  namespace and see trying to execute it without specifying a namespace fails.


References
==========

None.
