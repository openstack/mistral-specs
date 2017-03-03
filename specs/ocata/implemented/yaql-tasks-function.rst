..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================
Yaql Tasks Function
===================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/yaql-tasks-function

This new function will allow user to get a list of tasks matching certain
filters. For example: only task in state ERROR from the current execution.

Work on this draft started before **Jinja2** support was added. That said, a
user will be able to use this function both as part of **YAQL** expression and
as part of **Jinja2** expression.


Problem description
===================

There's no easy way in the error handler to know which task failed and failure
information.

Use Cases
---------

* When an error happens and default on-error is triggered, decide how to handle
  it according to the task that failed, even if it is in a nested workflow.

* Be able to get all tasks that failed in a workflow easily. Including nested
  tasks.

Proposed change
===============

Add a new **YAQL** function called **tasks**, which will be similar to the
**task** function we have today. The main difference is that **tasks** function
will return a list and will have more querying options.

Positional parameters for the new function:

#. ``wf-execution-id`` (optional) - will allow to get tasks information from a
   specific workflow execution (either the current execution or a different
   one), if not passed, it will list all tasks.
#. ``recursive`` (optional. Default: false) - if true treat all tasks in
   nested workflows as if they where also a part of all higher level
   wf-executions. Relevant mostly when filtering using ``wf-execution-id``.
#. ``state`` (optional) - get only tasks with the given state, for example
   all ERROR tasks. If not passed, it will list all tasks.
#. ``flat`` (optional. Default: false) - if true, only list the tasks that
   match at least one of the next conditions:

   * tasks of type action
   * tasks of type workflow, that also have a different state than the one
     of the nested workflow execution that was executed because of the task.


workflow with **YAQL** function example:

 ::

   ---
   version: '2.0'
   wf:
     type: direct
     input:
       - tasks_in_error: []
     tasks:
       my_example:
         action: std.noop
         publish:
           # publish all tasks in state ERROR of the current execution only
           tasks_in_error: <% tasks(execution().id, ERROR) %>

When running 'mistral task-get-published $TASK_ID' where TASK_ID is the ID
of my_example task execution, mistral will return:

 ::

  {
    "tasks_in_error": []
  }


The items in the list (when the list isn't empty) are from the same type and
structure as returned today from the task function.

Alternatives
------------

The parameters order and function name can be different.
We might want to pass a list of states and not just one.

Data model impact
-----------------

This change doesn't have to influence the data model.

However, right now the behavior is that a task state is updated before
publishing values are evaluated, and that is what is visible from the context
of the function. We might want to change it in the future.

REST API impact
---------------

None.

End user impact
---------------

The user will have a new function that can be used as part of **YAQL** or
**Jinja2** expressions.

Performance Impact
------------------

There is a possibility each call for this new function will trigger multiple
DB queries. The more nested the workflow is, the more queries. This is not
very efficient, but we can improve this later on if necessary.

Another thing that might happen is, if the user will not filter the tasks,
the amount of data might cause a timeout.

Example for clarity - a workflow and the published result
 ::

  ---
  version: '2.0'

  wf:
    type: direct
    input:
      - tasks_in_error: []
    tasks:
      my_example:
        action: std.noop
        publish:
          # publish all the tasks of the current execution only
          all_tasks_in_execution: <% tasks(execution().id) %>

The result of publishing:

 ::

  {
    "all_tasks_in_execution": [
        {
            "state_info": null,
            "name": "my_example",
            "spec": {
                "action": "std.noop",
                "version": "2.0",
                "type": "direct",
                "name": "my_example",
                "publish": {
                    "all_tasks_in_execution": "<% tasks(execution().id) %>"
                }
            },
            "state": "SUCCESS",
            "result": null,
            "published": {},
            "id": "a8b4787c-5b10-488a-8539-8370488fed8c"
        }
    ]
  }

To summarize the issue:
  Right now the state of the task when publishing is SUCCESS and not RUNNING,
  even though a user might expect it to be RUNNING. We don't have to do
  anything about it, but we should document this really well and say this might
  change in the future.

Deployer impact
---------------

None.


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

* implement the new function and filters based on argument position in the
  function.
* write tests.

Dependencies
============

None.


Testing
=======

Examples for the next scenario: a mistral setup with 3 workflow executions,
each execution started from a different workflow (just to make it more easy):

::

  execution of workflow1                      (workflow execution id = 1)
  |-top_level_wf1_task_1          SUCCESS     (workflow execution id = 1)
  |---second_level_wf1_task_1     SUCCESS     (workflow execution id = 2)
  |-----third_level_wf1_task_1    SUCCESS     (workflow execution id = 3)
  |-----third_level_wf1_task_2    SUCCESS     (workflow execution id = 3)
  |-----third_level_wf1_task_3    ERROR       (workflow execution id = 3)
  |---second_level_wf1_task_2     SUCCESS     (workflow execution id = 2)
  |---second_level_wf1_task_3     SUCCESS     (workflow execution id = 2)
  |-top_level_wf1_task_2          SUCCESS     (workflow execution id = 1)

  execution of workflow2                      (workflow execution id = 1001)
  |-top_level_wf2_task_1          SUCCESS     (workflow execution id = 1001)
  |-top_level_wf2_task_2          SUCCESS     (workflow execution id = 1001)

  execution of workflow3                      (workflow execution id = 300001)
  |-top_level_wf3_task_1          ERROR       (workflow execution id = 300001)
  |---second_level_wf3_task_1     ERROR       (workflow execution id = 300002)
  |-----third_level_wf3_task_1    SUCCESS     (workflow execution id = 300003)
  |-----third_level_wf3_task_2    SUCCESS     (workflow execution id = 300003)
  |-----third_level_wf3_task_3    ERROR       (workflow execution id = 300003)
  |---second_level_wf3_task_2     SUCCESS     (workflow execution id = 300002)
  |---second_level_wf3_task_3     SUCCESS     (workflow execution id = 300002)
  |-top_level_wf3_task_2          ERROR       (workflow execution id = 300001)


Here is a table representation with additional info:

::

  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | top level execution id | execution id | task name                    | task state     | task type     | inner execution state if exist  | inner execution id if exist  |
  +========================+==============+==============================+================+===============+=================================+==============================+
  | 1                      | 1            | top_level_wf1_task_1         | SUCCESS        | WORKFLOW      | SUCCESS                         | 2                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 1            | top_level_wf1_task_2         | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 2            | second_level_wf1_task_1      | SUCCESS        | WORKFLOW      | ERROR                           | 3                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 2            | second_level_wf1_task_2      | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 2            | second_level_wf1_task_3      | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 3            | third_level_wf1_task_1       | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 3            | third_level_wf1_task_2       | ERROR          | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1                      | 3            | third_level_wf1_task_3       | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1001                   | 1001         | top_level_wf2_task_1         | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 1001                   | 1001         | top_level_wf2_task_2         | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300001       | top_level_wf3_task_1         | ERROR          | WORKFLOW      | ERROR                           | 300002                       |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300001       | top_level_wf3_task_2         | ERROR          | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300002       | second_level_wf3_task_1      | ERROR          | WORKFLOW      | ERROR                           | 300003                       |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300002       | second_level_wf3_task_2      | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300002       | second_level_wf3_task_3      | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300003       | third_level_wf3_task_1       | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300003       | third_level_wf3_task_2       | SUCCESS        | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+
  | 300001                 | 300003       | third_level_wf3_task_3       | ERROR          | ACTION        | -                               | -                            |
  +------------------------+--------------+------------------------------+----------------+---------------+---------------------------------+------------------------------+

reminder: the order of the function arguments is:

1. wf-execution-id
2. recursive
3. state
4. flat

calling 'tasks()' will:
  return all 18 tasks.

calling 'tasks(1)' or 'tasks(1, false)' will:
  return 2 tasks of workflow1 execution (only tasks with execution id of 1):
    * top_level_task_1
    * top_level_task_2

calling 'tasks(1, true)' will:
  return all 8 tasks of the workflow1 workflow execution.

calling 'tasks(1001)' or 'tasks(1001, true)' or 'tasks(1001, false)' will:
  return the 2 tasks of workflow2 execution.

calling 'tasks(1, true, ERROR)' will:
  return 1 task of workflow1 execution:
    * third_level_wf1_task_3

calling 'tasks(1, false, ERROR)' will:
  return an empty list.

calling 'tasks(300001, true, ERROR)' or 'tasks(300001, true, ERROR, false)'
 will:
  return 4 task of workflow3 execution:
    * top_level_wf3_task_1
    * second_level_wf3_task_1
    * third_level_wf3_task_3
    * top_level_wf3_task_2

calling 'tasks(300001, true, ERROR, true)' will:
  return 2 task of workflow3 execution:
    * third_level_wf3_task_3
    * top_level_wf3_task_2

calling 'tasks(1, true, SUCCESS, true)' will:
  return 6 tasks of workflow1 execution:
    * top_level_wf1_task_2
    * second_level_wf1_task_1
    * second_level_wf1_task_2
    * second_level_wf1_task_3
    * third_level_wf1_task_1
    * third_level_wf1_task_3


References
==========

None.
