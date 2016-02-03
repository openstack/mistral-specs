..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================
Customize message for Transition
================================

https://blueprints.launchpad.net/mistral/+spec/mistral-fail-transition-message


Problem description
===================

Currently, "fail" command fails the workflow and the user needs to check the
different entities and flow to find why workflow has been failed. So, the
workflow execution is failed but there is no meaningful error message.

Use Cases
---------

As a user, I want to provide customized message for fail/success/pause
transition in 'on-success', 'on-complete' and 'on-error'.


Proposed change
===============

To solve this problem, I would like to add 'msg' input argument for
fail/success/pause commands. This argument will be publish to the
context before running fail/success/pause. Please consider following
example::

    ...
    tasks:
      t1:
        action: ...
        on-success:
          - fail(msg='var1 is null.'): <% $.var1 = null %>
          - succeed(msg='var1 is not null.')

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

None

End user impact
---------------

User can pass 'msg' argument for fail/success/pause commands. This argument
will be optional.

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

hardik <hardik.parekh@nectechnologies.in>

Work Items
----------

* Add input argument 'msg' for fail/success/pause commands.


Dependencies
============

None


Testing
=======

Tests should cover all the scenarios mentioned in use cases section.


References
==========

https://review.openstack.org/#/c/276625/
