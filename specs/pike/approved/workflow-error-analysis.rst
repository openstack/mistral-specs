..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=======================
Workflow Error Analysis
=======================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-error-analysis

This specification will outline the need for error analysis command or method
within Mistral.


Problem description
===================

Currently there is not a central way or single command which can be issued to
determine the root cause of an error that has occurred upon failure of a
mistral workflow. The proposed functionality would give the developer and
operator a method which can help debug errors which may stem from syntax errors
within the workbook or reveal actual bugs, by reporting the necessary
information from the execution to the client.


Use Cases
---------

The main uses for this feature would involve post workflow runs which involve
but not limited to OpenStack post deployment and workflow run investigation.


Proposed change
===============

Provide a command line interface and public API which the operator can use to
trigger the analysis of errors.

The table below is a draft example and subject to change once reviews are
complete.

* 'mistral report-generate <workflow id>'

+-------------------------------------------------------------------+
|Field                 |   Value                                    |
+======================+============================================+
|Workflow_name         | my_workflow                                |
+----------------------+--------------------------------------------+
|Workflow_ID           | xxxxx-xxxx-xxx-xxxxxxx                     |
+----------------------+--------------------------------------------+
|Workflow_State        | [Error | Success ]                         |
+----------------------+--------------------------------------------+
|\**Workflow_State_info| \***<task_name: cause>                     |
+----------------------+--------------------------------------------+
|Task_name             | my_task                                    |
+----------------------+--------------------------------------------+
|Task_ID               | xxxxx-xxxx-xxx-xxxxxxx                     |
+----------------------+--------------------------------------------+
|Task_State            | [Error | Success]                          |
+----------------------+--------------------------------------------+
|Task_State_info       | <cause>                                    |
+-------------------------------------------------------------------+

* 'mistral report-generate --include-trace <workflow id>'

+---------------------------------------------------------------------+
|Field                   |   Value                                    |
+========================+============================================+
|Workflow_name           | my_workflow                                |
+------------------------+--------------------------------------------+
|Workflow_ID             | xxxxx-xxxx-xxx-xxxxxxx                     |
+------------------------+--------------------------------------------+
|Workflow_State          | [Error | Success ]                         |
+------------------------+--------------------------------------------+
|\**Workflow_State_info  | \***<task_name: cause>                     |
+------------------------+--------------------------------------------+
|Task_name               | my_task                                    |
+------------------------+--------------------------------------------+
|Task_ID                 | xxxxx-xxxx-xxx-xxxxxxx                     |
+------------------------+--------------------------------------------+
|Task_State              | [Error | Success]                          |
+------------------------+--------------------------------------------+
|Task_State_info         | <cause>                                    |
+------------------------+--------------------------------------------+
|\****Workflow_traceback |    my_workflow ERROR                       |
|                        |      task_2 ERROR                          |
|                        |        workflow: my_other_workflow         |
|                        |          task_b: Error                     |
|                        |            action: somethingbroken         |
+---------------------------------------------------------------------+

\** State info would report <None> in the case where no error is generated.

\*** Task name and cause, the cause would be evaluated from an enum value.

\**** Workflow traceback would report a more verbose output of errors this
output could be controlled with a cli switch --include-trace. Without the
flag, the operator would just receive the enum value with a brief description.

example:
 * E101 -- task <task name> contains syntax error
 * E120 -- task <task name> missing input
 * E201 -- action failed to complete




Alternatives
------------

The current method of determining a error would involve looking through the
workflow execution id list to determine what is in an error state.

* 'mistral task-list <workflow execution id>' and see what are in ERROR
* for each failed task execution run:
   - 'mistral action-execution-list' and see what are in ERROR
* for each failed action run:
   - 'mistral action-execution-get-output <id>' to see the description of the
     error
* for each failed task execution of type Workflow, find the sub-workflow
  execution ID, and go back to the first bullet.

Data model impact
-----------------

None.

REST API impact
---------------

This is still in discussion.

* A separate REST API endpoint to build reports on the current status of
  execution and/or error analysis

End user impact
---------------

The end user would have a newly documented method/function to call to start the
error analysis.


Performance Impact
------------------

If this is implemented on the server side the performance impact should be
greatly reduced as the need for ReST calls would be drastically reduced.

Deployer impact
---------------

This would provide additional information to help the operator correct errors
in the deployment, or it will provide enough information which can be attached
to a bug report to help development correct the offending source.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  toure

Other contributors:
  rakhmerov

Work Items
----------

* Create new Mistral engine error analysis functionality.
* Update python-mistralclient to include new API changes.
* Update documentation to explain usage.
* Create CI scripts/jobs to mimic error in workflows.


Dependencies
============

None.

Testing
=======

Functional tests that imitate workflow failures and make sure that we
get the right report.


References
==========

None.
