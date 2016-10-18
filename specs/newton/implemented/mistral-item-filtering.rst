..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================
Items filtering in Mistral
==========================

https://blueprints.launchpad.net/mistral/+spec/mistral-items-filtering


Problem description
===================

Currently, we don't have any support for items filtering on the server side
which affects performance badly. In future, we may have thousands of actions.
So, we should be able to filter items before transferring them over the
network. Also, it is very difficult to find specific data in the list of
returned items. For example, we have a lot of 'standard' OpenStack actions.
So it is not very convenient to look through all of them to find actions
for nova.

Use Cases
---------

As a user, I want to have an ability to filter data.


Proposed change
===============

To solve this problem, I would like to implement customized filter for
database. This filter will support "in", "nin", ">", ">=", "<" and "<="
operations. Also, new parameters will be allowed in REST API. These
parameters are the name of columns by which users are allowed to filter
data.

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

1. Gets only those actions which have '<some_value>' as <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=<some_value>


2. Gets only those actions which have '<some_value_1>' or '<some_value_2>' as
   <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=in:<some_value_1>,<some_value_2>


3. Gets only those actions which have not '<some_value_1>' or '<some_value_2>'
   as <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=nin:<some_value_1>,<some_value_2>


4. Gets only those actions which have not <some_value> as <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=neq:<some_value>


5. Gets only those actions which have greater value than <some_value> as
   <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=gt:<some_value>


6. Gets only those actions which have greater than or equal to <some_value> as
   <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=gte:<some_value>


7. Gets only those actions which have less value than <some_value> as
   <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=lt:<some_value>


8. Gets only those actions which have less than or equal to <some_value> as
   <column_name> value.

GET http://127.0.0.1:8989/v2/actions?<column_name>=lte:<some_value>

Same changes are proposed for workflows, workbooks, cron triggers, executions,
tasks etc.

End user impact
---------------

User can add new option in CLI. For instance ::

    mistral action-list --filter <column-name>=<op>:<some_value>

Here '<op>' can be "eq", "neq", "gt", "gte", "lt", "lte", "in" or "nin".
Multiple values can be provided by using ";" separator.

Performance Impact
------------------

Only requested/filtered data will be fetched from database and transmitted over
network. So, it will improve the response time for the request.

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

* Add new parameter to REST api.
* Add new option for CLI.

Dependencies
============

None


Testing
=======

Tests should cover all the scenarios memtioned in use cases section.


References
==========

[1]: https://review.openstack.org/269971
[2]: http://specs.openstack.org/openstack/api-wg/guidelines/pagination_filter_sort.html
