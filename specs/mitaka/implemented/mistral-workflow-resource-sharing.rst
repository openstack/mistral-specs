..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================================
Support workflow sharing in Mistral
===================================

https://blueprints.launchpad.net/mistral/+spec/mistral-workflow-resource-sharing


Problem description
===================

Currently, we support creating public scope resource in Mistral, a public
resource(e.g. workflow) could be visible and used by any other tenant of the
system. The motivation of this feature is to avoid too many 'noisy' workflows
when you do ``mistral workflow-list`` in CLI, because you will passively see
all the resources with 'public' property, which you don't care about and will
never use, the situation will get worse especially in scenario of public
cloud.

Use Cases
---------

* As a tenant, I want to share my workflows to a specific tenant, rather than
  all other tenants in the system.

* As a tenant, I want to have the capability to accept or reject workflows
  shared to me.

* As a tenant, I can see the workflows list containing all of the following:
  all public workflows, my own workflows and the workflows that I am a member
  of.


Proposed change
===============

To solve those problems, I propose adding new resource sharing API for this
feature, please see detailed information in the following sections.

Users should always use UUID for using workflow sharing feature, because using
name will cause a lot of confusion and lead to plenty of bugs, e.g. different
tenants could have same name workflows, they can share these workflows to
another tenant, who will be confused when he operates with the workflow name.
Workflow UUID in API has been supported[1] in Mistral.

Alternatives
------------

None

Data model impact
-----------------

A new table is needed for this feature, the following table constructs would
suffice ::

    __tablename__ = 'resource_members_v2'
    __table_args__ = (
        sa.UniqueConstraint(
            'resource_identifier',
            'resource_type',
            'member_id'
        ),
    )

    id = mb.id_column()
    resource_identifier = sa.Column(sa.String(80), nullable=False)
    resource_type = sa.Column(
        sa.String(50),
        nullable=False,
        default='workflow'
    )
    project_id = sa.Column(sa.String(80), default=security.get_project_id)
    member_id = sa.Column(sa.String(80), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, default="pending")

Database migration is also needed.

REST API impact
---------------

1. Shares the workflow to a new member.

POST http://127.0.0.1:8989/v2/workflows/<shared-workflow-uuid>/members

request body::

    {'member_id': XXX}

response::

    {
        'resource_identifier': <workflow-id>,
        'resource_type': 'workflow',
        'project_id': <ower-id>,
        'member_id': <member-id>,
        'status': 'pending'
    }

2. Sets the status for a workflow member.

PUT http://127.0.0.1:8989/v2/workflows/<shared-workflow-uuid>/members/<member-id>

request body::

    {'status': <pending/accepted/rejected>}

Only user with whom this workflow is shared could make this call, to
accept or reject the sharing, or remain what the status was. Other users
making this call may get HTTP 404 status code.

3. Shows workflow member details.

GET http://127.0.0.1:8989/v2/workflows/<shared-workflow-uuid>/members/<member-id>

Response body is a single workflow member entity, user must be the owner
or a member of the workflow.

4. Return all members with whom the workflow has been shared.

GET http://127.0.0.1:8989/v2/workflows/<shared-workflow-uuid>/members

If a user with whom this workflow is shared makes this call, the member
list contains only information for that user.
If a user with whom this workflow has not been shared makes this call, the
call returns the HTTP 404 status code.

5. Deletes a member from the member list of a workflow.

DELETE http://127.0.0.1:8989/v2/workflows/<shared-workflow-uuid>/members/<member-id>

Users making this call must be the owner of the workflow. Please note,
check should be done before the member relationship is deleted, since
after deletion, other users can not use that workflow any more, which may
cause error to existing executions or cron-triggers.

End user impact
---------------

Besides the new API, users can use new commands in CLI for resource sharing
feature. For instance::

    mistral resource-member-create --type workflow --id <workflow-id> \
    --member <member-id>

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

kong <anlin.kong@gmail.com>

Work Items
----------

* Add new db schema for resource_member.
* Add db operations for resource members.
* Add new API for workflow sharing.
* Including workflows shared to user, when user query workflows.


Dependencies
============

None


Testing
=======

Tests should cover all the scenarios memtioned in use cases section.


References
==========

[1]: https://blueprints.launchpad.net/python-mistralclient/+spec/support-id-in-workflow-operation
