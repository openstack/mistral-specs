..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===============================================
Publish/output in case of task/workflow failure
===============================================

https://blueprints.launchpad.net/mistral/+spec/mistral-publish-on-error

Currently it is not possible to provide any reasonable output in case of a
task or workflow failure. Implementing this would greatly simplify error
handling in workflows.


Problem description
===================

This blueprint is a proposal to introduce two new attributes,
publish-on-error for tasks and output-on-error for workflows for this purpose.


Use Cases
---------

* As a user, I would like to define a workflow with a generic error
handler task.
* As a user, I would like to simplify error handling in my complex
workflow system.

Proposed change
===============

To solve the problem I would like to introduce the following new task and
workflow attributes:

* Task - publish-on-error: Any data structure arbitrarily containing YAQL
   expressions that defines output of a task to be published into workflow
   context if it goes into error state.

* Workflow - output-on-error: Any data structure arbitrarily containing YAQL
   expressions that defines output of a workflow to be returned if it goes into
   error state.

Example workbook:

.. code-block:: yaml

    workflows:
        main:
            tasks:
                task_1:
                    workflow: sub-workflow
                    publish-on-error:
                        failure_cause: <% task(task_1).result.failure_cause %>
                        detailed_cause: <% task(task_1).result.detailed_cause %>
                    on-error:
                        - error-handler
                task_2:
                    ...
                    publish-on-error:
                        failure_cause: <% task(task_2).result.failure_cause %>
                        detailed_cause: <% task(task_2).result.detailed_cause %>
                    on-error:
                        - error-handler

                error-handler:
                    action: send_email
                    input:
                        body: |
                            <% $.failure_cause %>
                            Details:
                            <% $.detailed_cause %>

        sub-workflow:
            output:
                result: <% $.result %>
            output-on-error:
                failure_cause: <% $.failure_cause %>
                detailed_cause: <% $.detailed_cause %>

            tasks:
                task1:
                    ...
                    publish-on-error:
                        failure_cause: "Failure in sub-workflow.task1!"
                        detailed_cause: <% task(task1).result %>
                    on-success:
                        - task2
                task2:
                    ...
                    publish-on-error:
                        failure_cause: "Failure in sub-workflow.task2!"
                        detailed_cause: <% task(task2).result %>


Alternatives
------------

N/A

Data model impact
-----------------
Two new fields introduced:
* Task spec - publish-on-error
* Workflow spec - output-on-error

REST API impact
---------------
None

End user impact
---------------
Workflow language additions that allow to handle errors in a more flexible way.
Existing workflows will work without any change.

Performance Impact
------------------
None

Deployer impact
---------------
None


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  István Imre <istvan.imre@nokia.com>

Other contributors:
  Endre János Kovács <endre.kovacs@nokia.com>

Work Items
----------
* add publish-on-error to task spec
* add output-on-error to workflow spec
* documentation


Dependencies
============
None

Testing
=======
* new engine test for the two new attributes


References
==========
None
