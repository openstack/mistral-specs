===============================
Allow env update on task re-run
===============================

https://blueprints.launchpad.net/mistral/+spec/mistral-rerun-update-env

Problem description
===================
On rerunning (and resuming) a workflow execution, allow changes to the
environment variables that were provided at the start of workflow execution.

Use Cases
---------
Given the use case where a workflow execution failed because of environment
related issue(s) (i.e. endpoint unavailable, etc.), it is possible that as
part of resolving the environment related issue(s), the endpoint is replaced
(i.e. different host/ip) or that the token passed as credential has expired.
Endpoints and credentials can be passed on workflow invocation under the env
param and then accessed by workflow tasks using the env() function. In these
circumstances, the user will need to be able to update the env variables prior
to re-running the workflow task(s). This also applies to workflow that are
manually paused (i.e. for maintenance) and now resumed but the token passed as
credential in the env has expired.

Proposed change
===============
To change environment variables, this will be a two step process. First is to
overlay the new set of env variables to the workflow execution context so any
new task executions will pick up the changes. Second to overlay the new set
to the in context of the existing tasks to be rerun. Any existing tasks that
have completed successfully will not be modified.

Alternatives
------------
None

Data model impact
-----------------
- New env property for the Task API resource model to pass the new set of
  environment variables.

REST API impact
---------------
Update to the env is only permitted on task re-run or workflow resume.

For workflow resume, the PUT method of the execution controller will be
affected. The user will pass the new set of environment variables via
params in the Execution resource model. Then the put operation for the
executions controller will pass the updated env to resume_workflow (i.e.
rpc.engineclient().resume_workflow(wf_ex_id, env=env)). The
resume_workflow method will merge the new set of env to the workflow
execution appropriately.

The following is the data for the PUT request to the execution controller.

.. code-block:: json

    {
        "state": "RUNNING",
        "params": "{'env': {'k1': 'v1'}}"
    }

For task re-run, the PUT method of the task controller will be affected.
The user will pass the new set of environment variables via the env
property in the Task resource model. Then the put operation for the
tasks controller will pass the updated env to rerun_workflow (i.e.
rpc.engineclient().rerun_workflow(wf_ex_id, task_ex_id, env=env)). The
rerun_workflow method will merge the new set of env to the workflow
execution and the task execution appropriately.

The following is the data for the PUT request to the task controller.

.. code-block:: none

    {
        'state': 'RUNNING',
        'reset': True,
        'env': '{"k1": "v1"}'
    }

End user impact
---------------
- Add --env option to `mistral execution-update` to pick up a json string or
  path to a json file containing the list of variables to update.
- Add --env option to `mistral task-rerun` to pick up a json string or
  path to a json file containing the list of variables to update.

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
    m4dcoder

Work Items
----------
- Add DB API method to update env in execution.
- Update resume_workflow in default engine.
- Update rerun_workflow in default engine.
- Update PUT in execution controller.
- Update Task API resource model.
- Update PUT in task controller.
- Update execution-update command in mistral client.
- Update task-rerun command in mistral client.

Dependencies
============
None

Testing
=======
- Test that environment is updated and workflow can rerun successfully.
- Test update of workflow execution and task execution in different states.
  Test exception cases where certain states are not allowed (i.e. SUCCESS).

References
==========
None
