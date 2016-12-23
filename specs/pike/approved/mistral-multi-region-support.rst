..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================================
Support region in OpenStack actions
===================================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-multi-region-support

This blueprint intends to support specifying region name for OpenStack
actions, so that authorized user could run OpenStack actions within different
OpenStack regions in one workflow, which is extremely userful for operators
when they want to execute maintainance tasks across different regions within
one workflow.


Problem description
===================

Currently, Mistral end user could specify region name or target region name
when running OpenStack workflow, which means all the tasks inside the workflow
have to be running within that specific region. It's impossible to run
different tasks in different regions.

Use Cases
---------

* User with credential in region-1 can specify region-2 for the whole
  workflow (Keystone is shared between different regions).

* User with credential in region-1 can specify different region in different
  tasks.


Proposed change
===============

The basic idea is simple, support 'region' as an extra input param for all
OpenStack actions.

1. Add a config option called ``modules_support_region``, the value will be
   list of module names for which the 'region' input param will be add to each
   of its actions. The reason for adding this option is, there may be some
   OpenStack services (e.g. Keystone) already support region(or similar
   concept) in action input params, we should not add a param with same
   meaning, e.g. if Keystone is shared between regions in OpenStack
   deployment, 'keystone' should be excluded from the list.

2. Insert 'region' as an optional input param when registering OpenStack
   actions.

Alternatives
------------

As mentioned in the problem description section, it's impossible to do multi-
region workflows without this feature.

Data model impact
-----------------

This change doesn't have to influence the data model.

REST API impact
---------------

None.

End user impact
---------------

With this change, users could specify region name as action input.

Performance Impact
------------------

None.

Deployer impact
---------------

When upgrade, deployer should run ``tools/sync_db.py`` script to delete all
OpenStack actions and re-create again. 'region' will be added as input param
automatically.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Lingxian Kong <anlin.kong@gmail.com>

Work Items
----------

* Add 'region' as action input param for modules specified in
  ``modules_support_region`` options. Use 'region' to construct OpenStack

* service client.


Dependencies
============

None.


Testing
=======

* write tests to make sure 'region' is supported for configured OpenStack
  modules.

* write tests to make sure 'region' is properly used to construct OpenStack
  service client.


References
==========

None.
