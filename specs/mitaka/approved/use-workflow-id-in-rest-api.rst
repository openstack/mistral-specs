..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=========================================
Workflow UUID support in Mistral REST API
=========================================

https://blueprints.launchpad.net/mistral/+spec/use-workflow-id-in-rest-api


Problem description
===================

Currently, we identify a workflow by its name, of course, the workflow name is
unique within a tenant's scope. However, when we use 'public' workflows or we
want to get benifits from workflow sharing feature[1], we may see more than
one workflows with the same name (you can see a related bug which has been
fixed here[2]). Even worse, users will never see other 'same-name' workflows
when performing ``mistral workflow-get <name>`` command, since it always
returns the first one.

Look at almost all other projects, they always use UUID as globally unique
resource identifier, especially in the REST API, the resource name is a string
that can be duplicated throughout the whole system, and may be changed
frequently as the time goes by.

So, I propose we use UUID as the workflow global unique identifier in the REST
API. What's more, we can consider using UUID for other resources after that.

Use Cases
---------

* As a user, I want to see the definition of a public scope workflow, whose
  name is the same with one of my private workflows or another public
  workflow.

* As a user or application developer, I want to send REST API to Mistral with
  resource UUID contained, rather than resource name.


Proposed change
===============

We need to support workflow UUID as a parameter of pecan WorkflowsController
related methods(GET, PUT, DELETE), we still support workflow name for backward
compatibility, the magic will be happened in the db api layer. At the
meanwhile, workflow UUID needs to be exposed to end users, using which users
could do operations they want.

Things will be a little complicated for PUT method. Before, when we want to
update a workflow definition, Mistral only accepts URL like
http://localhost:8989/v2/workflows and the new workflow definition content as
request body, which means workflow name is an identifier when updating
workflow definition, and can't be changed. In order to support UUID, a new
parameter with an appropriate default value will be added to PUT method, with
the UUID, workflow name can be changed. In addition, when updating a workflow
with UUID provided, only one workflow definition could be contained in request
body.

Since UUID is so important right now, users should see that both via REST API
or Mistral client, a good news is, UUID has already be supported from both
server side and client side[3].

Changes should also be made for db interface, operations should be supported
based on UUID.

Alternatives
------------

Without the UUID support in REST API, those problems mentioned in the first
section can't be solved totally.

Data model impact
-----------------

None

REST API impact
---------------

All the REST API requests for workflow resource will support UUID, the request
and response body are the same with before, the only exception to this is PUT
HTTP method.

When updating a workflow with UUID provided, only one workflow definition
could be contained in request body.

End user impact
---------------

It's strongly recommended that users use UUID in URL of HTTP request or in the
command line.

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
  kong <anlin.kong@gmail.com>

Work Items
----------

* Add UUID support for GET, PUT, DELETE mothod of workflow REST API.


Dependencies
============

None


Testing
=======

* Test the UUID support in REST API and/or Mistral client side.


References
==========

[1]: https://blueprints.launchpad.net/mistral/+spec/mistral-resource-sharing

[2]: https://bugs.launchpad.net/python-mistralclient/+bug/1518276

[3]: https://review.openstack.org/248031
