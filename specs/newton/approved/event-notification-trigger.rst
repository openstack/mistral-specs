..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=================================================
Run workflow in response to an event notification
=================================================

https://blueprints.launchpad.net/mistral/+spec/event-notification-trigger

This spec adds support to run Mistral workflows in response to AMQP events.
This will provide cloud operators the ability to automate
their operations by running workflows in response to specific notification
events posted on an AMQP topic, including those emitted by OpenStack
notifications.  For example of OpenStack notifications, see:
https://wiki.openstack.org/wiki/SystemUsageData

Note: The solution provided in this spec is generic to any AMQP
notification system supported by oslo.messaging and therefore there no strict
dependency on OpenStack. However, the use cases sited in this spec are
centered around OpenStack.


Problem description
===================

As things happen within OpenStack, OpenStack components can be configured to
emit notification events on the messaging bus. This includes events such as
when a server instance is created or deleted or when an image is activated
or deleted. When these events occur, operators may want to perform additional
functions for their clouds that are not provided by base OpenStack. By adding
support within Mistral to run workflows in response to these events,
it gives operators a means to perform these additional functions using a
reliable and supported mechanism all from within OpenStack. Just as cron
triggers give operators this ability based on time, this will give operators
this ability based on real time events.

To see a prototype demo, see the openstack summit presentation:
https://www.openstack.org/videos/video/using-openstack-to-clean-up-after-itself-automatically-run-mistral-workflows-in-response-to-openstack-notifications

Use Cases
---------

This function will enable a wide variety of use cases. To list just a few:

* As an operator, i need to clean up resources when a tenant/project
  is deleted.

* As an operator, i need to add a user or modify groups in response to a
  federated user login.

* As an operator, i need to have server instances expire after a given
  amount of time.

Given the rich set of Mistral actions, such as std.http, the operator is
not limited to just OpenStack functions.  For example, a server instance
delete or create might trigger a call to the operator's billing systems
or network switches.


Proposed change
===============

This change will allow operators to create an event trigger to run a given
workflow in response to a specific OpenStack event. The operator will be able
to create this trigger using standard OpenStack methods, such as using a
new REST API or CLI.
The operator will provide the following information at the time of creating the
workflow event trigger:

* The OpenStack event that should trigger the worflow.  This information
  can be found in each services configuration file (eg. nova.conf).

  * Messaging exchange, ie. ``nova``, ``glance``, etc.

  * Messaging topic, typically this will be set to ``notifications``.

  * Notification event ie. ``compute.instance.create.end``, ``image.activate``,
    etc.

* The Mistral workflow to be run:

  * Either the workflow name or workflow id.

  * If the workflow has input or params those can be specified as
    well.

This information (among other things) is stored in the new event_triggers_v2
table.  See the database section for more information.

In addition, the change provides the REST API and CLI (both mistral and
openstack) to manage the event
triggers, such as list, update, and delete.

A new Mistral service will be created that will listen on the provided
notification exchanges and topics, and in response to receiving the events,
will run the configured Mistral workflows.  See the Detailed Changes section
for details.

The horizon plugin will be updated to manage event triggers.

Note: This function does not enable other services to emit notification
events.  In order for this new service to receive events, those
events must be configured to be emitted using the OpenStack service's normal
event notification configuration.

Detailed Changes
----------------

To provide this support, the following changes will be made:

* Add new database table to store event triggers (see the database section).

* Add new REST API to perform list, create, update, delete operations on the
  event triggers (see the API section).

* Add new CLI commands to python-mistralclient to support list, create,
  update, and delete operations on the event triggers.

* Add new CLI command to the openstack client to support list, create, update,
  and delete operations on the event triggers.

* Add a new service which does the following:

  * Reads the database table to get a list of the events to listen for
    and their workflow mappings.

  * Starts an event listener on a thread to handle configured notification
    events from the database.  The event listener does the following:

    * Listens for notifications on the exchange and topic as specified in
      the database.

    * Determines which workflow to start based on the message event type and
      the project in the notification.  The query will be as follows:

      `select workflow_name, workflow_id where event=message.event_type and
      (project_id=message.project_id or scope=public)`

      Note: The above query is to show how the workflow is selected, this code
      may not always call the database, but rather have some type of cache.
      This will be determined during implementation.

      If no workflow is found for the event, then no action is taken.

    * Start the configured workflow passing in the workflow input and params
      if configured.  In addition, the notification event type
      and the message payload will be added to the params of workflow. This
      allows the workflow to retreive the event type and message payload as
      follows::

        event_type: <% execution().params.notification_event_type %>
        payload: <% execution().params.notification_payload %>

      See security context section below for more information on which
      security context is used.

    * When the API creates or deletes an event trigger a mistral
      notification event is emitted to tell the event listener code to update
      itself.

* Update the documentation.

* Update the mistral horizon plugin to manage event triggers.

The implementation is straight forward with the following details:

* You can have multiple workflows associated with the same event. All the
  workflows that are associated with the event are run, however there is no
  guarantee that they will run sequentially or an in any particular order.
  Therefore these workflows should not rely on the state of the other
  workflows that are triggered for the event.

* To prevent multiple executions of the same workflow from the same message id
  the listener code will do the following when an event is received::

   acquire a row lock on the event_triggers_v2 table
     for the appropriate row
     (row=topic, exchange, event, project (or public),
      and workflow of the
      event that was received)
   if row lock is acquired:
      query execution table for a workflow execution
         with a param containing the message id
      if query results = 0 rows:
         start the workflow putting
         the message id in the params
      else:
         discard message since it's already executing
      release row lock
   else:
      discard message since another process is processing it

  This allows for the listener code to be HA enabled or have multiple
  instances running.

Security
--------

There are 3 possible security contexts an event triggered workflow can run
under:

* The security context that is present on the event notification message.

* The trust token which is set by using the use_trust flag on the
  API.  This flag will use the calling user's security token to obtain a trust
  token for that user and stored in the event trigger
  database.  When the workflow is run, it will run on behalf of this user,
  similar to cron triggers.

* The Mistral service context.

The security context of the workflow is chosen as follows::

  If the event trigger is configured with the trust id:
    context = trust token
  else:
    if there is a security context associated with the message:
       context = message notification event context
    else:
       context = mistral service context


Alternatives
------------

* Use JSON file to map events to workflows rather than using the database.
  This idea is being discarded
  because it doesn't really scale very well and the file is harder to manage.

* Use the ceilometer notification plugin to forward the notifications to
  mistral to run workflows.  This would involve adding a webhook to
  mistral to receive the notifications rather than directly listening on the
  AMQP exchange.  For this particular blueprint having to manage the ceilometer
  service is too much overhead when we could just listen on the exchange
  directly and keep everything within mistral for those operators that what a
  quick and simple notification trigger. The webhook idea is interesting and
  deserves it's own blueprint and spec as there may be other
  use cases that should be considered along with more detailed description of
  the interactions.  I could see operators wanting to use this webhook
  who need a more sophisticated callback/notification system that does not
  necessarily rely on AMQP. It's possible that a webhook implementation
  could share a significant portion of the event trigger implementation and
  should be able to easily coexist giving operators a choice depending on
  their needs.

Data model impact
-----------------

A new table will be created to store the event information and the
workflow name or id to execute.

+----------------------+--------------+------+-----+---------+-------+
| Field                | Type         | Null | Key | Default | Extra |
+----------------------+--------------+------+-----+---------+-------+
| created_at           | datetime     | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| updated_at           | datetime     | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| scope                | varchar(80)  | YES  | MUL | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| project_id           | varchar(80)  | YES  | MUL | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| id                   | varchar(36)  | NO   | PRI | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| name                 | varchar(200) | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| workflow_name        | varchar(80)  | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| workflow_id          | varchar(36)  | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| workflow_input       | text         | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| workflow_input_hash  | char(64)     | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| workflow_params      | text         | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| workflow_params_hash | char(64)     | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| exchange             | varchar(80)  | YES  | MUL | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| topic                | varchar(80)  | YES  | MUL | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| event                | varchar(80)  | YES  | MUL | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+
| trust_id             | varchar(80)  | YES  |     | NULL    |       |
+----------------------+--------------+------+-----+---------+-------+


REST API impact
---------------

The following new rest API will be created.  Standard HTTP return codes
will be used:
https://github.com/for-GET/know-your-http-well/blob/master/status-codes.md

GET v2/event_triggers
~~~~~~~~~~~~~~~~~~~~~

Returns the list of event triggers the user has access to based on the
token and any public scoped event triggers.  Note this API does not
support pagination or other filtering/sorting parameters since the
number of these is expected to be small.

**Request**

  - Parameters: None
  - Body: None

**Response**

+ Success

  - Status Code: 200 OK
  - Body::

     {
         "event_triggers": [
             {
                 "created_at": "1970-01-01T00:00:00.000000",
                 "event": "compute.instance.create.end",
                 "exchange": "nova",
                 "id": "123e4567-e89b-12d3-a456-426655440000",
                 "name": "my-create-server-trigger",
                 "scope": "public",
                 "topic": "notifications",
                 "updated_at": "1970-01-01T00:00:00.000000",
                 "workflow_name": "my-server-created-workflow",
                 "trust_id": "84933f8acdc74760bb02c9b7d815b246",
                 "project_id": "b84f269ceb174862a44f9ebf2ae7b938"
             }
         ]
     }

+ Typical Errors

   - None.  If the user does have access to any event triggers an
     empty list will be returned.

GET v2/event_triggers/{id}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns the event trigger specified by {name}.

**Request**

- Parameters: None
- Body: None

**Response**

+ Success

  - 200 OK
  - Response body::

     {
         "event_triggers":
             {
                 "created_at": "1970-01-01T00:00:00.000000",
                 "event": "compute.instance.create.end",
                 "exchange": "nova",
                 "id": "123e4567-e89b-12d3-a456-426655440000",
                 "name": "my-create-server-trigger",
                 "scope": "public",
                 "topic": "notifications",
                 "updated_at": "1970-01-01T00:00:00.000000",
                 "workflow_id": "123f4567-e89b-12d3-a456-426655440000",
                 "workflow_name": "my-server-created-workflow",
                 "trust_id": "84933f8acdc74760bb02c9b7d815b246",
                 "project_id": "b84f269ceb174862a44f9ebf2ae7b938",
                 "workflow_params": "{}",
                 "workflow_input": "{\"key\":\"value\"}"
             }
     }


+ Typical Errors

  - 404 Not Found - Indicates the specified event trigger was not found.

POST v2/event_triggers
~~~~~~~~~~~~~~~~~~~~~~

Creates a new event trigger.

Note: id, project_id, created_at, and updated_at are not allowed
to be set.  If they are set on the request those values are ignored.
Scope can either have a value of "public" or "private".
The following properties are required:
event, exchange, topic, and either workflow_name or workflow_id.

**Request**

- Parameters: None
- Body::

     {
          "event": "compute.instance.create.end",
          "exchange": "nova",
          "name": "my-create-server-trigger",
          "scope": "public",
          "topic": "notifications",
          "use_trust": true,
          "workflow_id": "123f4567-e89b-12d3-a456-42665544000i0",
          "workflow_input": "{\"key\":\"value\"}"
     }

**Response**

+ Success

  - Status Code: 201 Created
  - Response body: Same as `GET v2/event_triggers/{name}`

+ Typical Errors

  - 400 Bad Request: Indicates there is a problem with the request body or
    the workflow does not contain required input parameters.  The
    response body faultstring will contain the reason.
  - 409 Conflict: Indicates the event trigger with the specified name
    already exists.
  - Error response body::

      {"faultstring": "<Reason>"}

PUT v2/event_triggers/{name}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Updates the event trigger for the specified event trigger name.  Since we allow
multiple workflows per event, exchange, topic, the only allowable change is
for the scope and for the use_trust flag.  Scope can only have a value
of "private" or "public".

Note: The only allowable change is for the scope and use_trust flag, if
other properties are specified they are ignored.

**Request**

- Parameters: None
- Body::

    {
       "use_trust": false,
       "scope": "public"
     }


**Response**

+ Success

  - Status Code: 200 OK
  - Body: Same as GET v2/event_triggers/{name} with the updated
    information.

+ Typical errors:

  - 400 Bad Request - Indicates there is a problem with the request body.
  - 404 Not Found - Indicates the specified event trigger was not found.
  - Error response body::

     {"faultstring": "<Reason>"}

DELETE v2/event_triggers/{name}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deletes the event trigger with the specified name.

**Request**

- Parameters: None
- Body: None

**Response**

+ Success

  - Status Code: 204 No Content.
  - Body: None

+ Typical Errors

  - 404 Not Found - Indicates the specified event trigger was not found.
  - Error response body::

     {"faultstring": "<Reason>"}

End user impact
---------------

The following new CLI will be added to the python-mistralclient:

* mistral event-trigger-create::

   Create new event trigger.

     positional arguments:
       name                  Event trigger name
       workflow_identifier   Workflow name or ID
       exchange              AMQP notification exchange name
       topic                 Notification topic
       event                 Notification event
       workflow_input        Workflow input (optional)

     optional arguments:
       -h, --help            show this help message and exit
       --params PARAMS       Workflow params
       --public              With this flag the event trigger will be marked as
                             "public".
       --use-trust           With this flag the event trigger will use the
                             user's trust token when running the workflows.

* mistral event-trigger-list::

   List all event triggers.

    optional arguments:
      -h, --help            show this help message and exit

* mistral event-trigger-delete::

   Delete event trigger.

    positional arguments:
       name        Name of event trigger(s).

* mistral event-trigger-update::

   Update an existing event trigger.

    positional arguments:
      name                  Event trigger name

    optional arguments:
      -h, --help            show this help message and exit
      --public              With this flag the event trigger will be marked as
                            "public".
      --use-trust           With this flag the event trigger will use the
                            user's trust token with running the workflows.

Also, update the openstack client (see mistral client above for details on
the supported parameters):

* openstack event trigger create
* openstack event trigger delete
* openstack event trigger list
* openstack event trigger update

Finally, update the bash completion script for mistral.

Performance Impact
------------------

There should be no impact to existing mistral functions.  There will be a lock
held on a row in the event_triggers_v2 to prevent multiple instances of the
same event message from running the workflow more than once.
See the `Proposed Change` section.

Deployer impact
---------------

There should be no impacts to the deployer.  This new function is enabled
automatically, however, nothing will run until someone adds an event trigger
to the table via the REST API or the CLI.  This is similar to the cron
triggers.

Implementation
==============

Assignee(s)
-----------

Primary assignee:

Other contributors:

Work Items
----------

* Implement the database:

  * Create a new migrations file that will create the table and indexes.
  * Update the database API.
  * Update the sqlalchemy model.

* Implement the event listener service.

* Implement the new REST APIs.

* Implement the new mistral and openstack CLIs.

* Implement changes to the horizon plugin to create, delete, display event
  triggers.

* Implement the unit tests.

* Implement functional tests for event listener, REST APIs, and CLI.

* Update the code to start the listener service.

* Update the documentation and readme.

Dependencies
============

There are no additional dependencies.

Testing
=======

Functional and unit test cases will be provided for both mistral and
python-mistralclient.

In addition to the normal tests that test the API, additional functional
testcases will be provided to test the actual running of a worklfow triggered
from an event.  Likely this will involve triggering a notification in the
testcase an ensuring the workflow is run correctly.  The details of this test
will be worked out during the implementation.


References
==========

No references.
