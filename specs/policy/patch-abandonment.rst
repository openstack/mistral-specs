=================
Patch Abandonment
=================

Goal
====

Provide a basic policy that core reviewers can apply to outstanding reviews. As
always, it is up to the core reviewers discretion on whether a patch should or
should not be abandoned. This policy is just a baseline with some basic rules.

Problem Description
===================

Mistral consists of a number of different git repositories and there are open
and stale patches that have not been updated in a long time. This can make it
hard to assess the current state of reviews, since any report is cluttered by
old and idle reviews.

When to Abandon
===============

If a proposed patch has sat idle for more than 180 days with a -1 from a
reviewer or CI. A core reviewer should abandon the change with a reference to
this policy.

The following message can be used when abandoning patches.

::

    Abandoning this patch per the Mistral Patch Abandonment guidelines
    (https://specs.openstack.org/openstack/mistral-specs/specs/policy/patch-abandonment.html).
    If you wish to have this restored and cannot do so yourself, please reach
    out via #openstack-mistral on freenode or the OpenStack Dev mailing list.

When NOT to Abandon
===================

If a proposed patch has no feedback but has a +1 from CI, a core reviewer
should not abandon such changes. This change should be reviewed and moved
forward towards being updated or merged.


Restoration
===========

Anyone should feel free to restore their own patches. If a change has been
abandoned, anyone can request the restoration of the patch by asking a core
reviewer on IRC in #openstack-mistral on freenode or by sending a request to
the openstack-dev mailing list. Should the patch again become stale it may be
abandoned again.

Alternative & History
=====================

This plan is based on similar approaches taken in other OpenStack projects,
such as TripleO. This plan was discussed on openstack-dev [1]_.

Implementation
==============

Author(s)
---------

Primary author:
  d0ugal

References
==========

.. [1] http://lists.openstack.org/pipermail/openstack-dev/2018-July/132073.html

Milestones
----------

Rocky

Work Items
----------

- Perform the initial cleanup and abandonment.
- Create a script to automate the process.

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
