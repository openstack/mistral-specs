..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=======================
Mistral Actions Library
=======================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-actions-api-separate-openstack-actions

This specification outlines a proposal to move the OpenStack actions to
mistral-extra and define a process for accepting other third party actions
in mistral-extra.


Problem description
===================

Mistral ships with a set of standard generic actions and a set of actions
specific to OpenStack. The OpenStack actions help improve the utility of
Mistral but including them in Mistral itself raises a number of limitations.

- Some users won't want OpenStack actions. (i.e. Mistral running outside
  OpenStack).
- Some users will only want specific OpenStack actions. (i.e. their deployment
  only includes certain OpenStack projects).
- OpenStack actions can easily become out of date as the OpenStack clients can
  evolve quickly. Releases to these actions require full Mistral releases.

The OpenStack actions make Mistral much more useful in OpenStack environments
but there isn't a clear place to collect or develop other Mistral actions.
Without a wider set of actions that integrate with other services and projects
Mistral is unlikely to become used more widely.


Use Cases
---------

- As an administrator and deployer I want control over the actions included
  with Mistral.
- As a developer I want a clear place to contribute to actions and add
  support for third party actions.
- As an end user I want my workflows to have access to a library of actions
  that allow my workflows to do more without having to create custom actions.


Proposed change
===============

This specification proposes moving the current OpenStack actions to the
mistral-extra repo, which can be then referred to as the Mistral actions
library. This repository will depend on mistral-lib, as being developed under
the `custom actions API spec <mistral-custom-actions-api.html>`_.

mistral-extra will contain a Python namespace for all the OpenStack actions,
this will likely be ``mistral_extra.openstack``. The action names will remain
as they are now to maintain backwards compatability. It will also allow other
actions to be added to this project if they meet the requirements.

For an action to be considered for mistral-extra it should be generic and
useful for a wide range of users and not specific to one user or project. There
should also be a way to automate the testing of this action to verify that it
continues to work over time. Without the ability to do an integration test the
actions will become impossible to maintain as the library grows. Generally
useful actions are also candidates to be included in Mistral itself with the
other ``std.*`` actions.

A configuration file will be added that allows users to specify which actions
they want to include. By default this config will match the existing behaviour
and include all OpenStack actions, but other actions will need to be enabled
for each project.


Alternatives
------------

Alternatively we could continue storing the actions in Mistral and third party
actions could be developed outside of Mistral entirely. This may work, but it
would make it much harder to grow a cohesive library that is easy to use.


Data model impact
-----------------

No data model changes are required.


REST API impact
---------------

No API changes are required.


Python API
----------

The mistral-extra repository will also provide a stable Python API that can be
used by action developers as a library. This will allow them to access the
OpenStack actions and extend or customise them. The API is still to be
determined but usage will likely look something like this.

::

    from mistral_extra import openstack

    class CustomNovaAction(openstack.NovaAction):

        def run(self, context):

            nova_client = self.get_client(context)
            # do something custom and return


Access to the Python clients for OpenStack projects will also be possible. This
will allow custom action developers to easily consume multiple OpenStack
clients.

::

    from mistral_extra import openstack
    from mistral_lib import actions

    class CustomAction(actions.Action):

        def run(self, context):

            nova_client = openstack.NovaAction.get_client(context)
            glance_client = openstack.GlanceAction.get_client(context)


End user impact
---------------

Users will primarily interact with the feature by customising the mistral-extra
config file. This will need to be documented.


Performance Impact
------------------

No performance impact.


Deployer impact
---------------

No additional steps will be required by default for deployers. However, they
will have greater control of their deployment and which actions are included
and available to users.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  d0ugal

Other contributors:
  None


Work Items
----------

- Copy OpenStack actions to mistral-extra
- Package and release mistral-extra and update Mistral to depend on it
- Remove OpenStack actions from mistral
- Update the documentation to reflect the configuration of mistral-lib


Dependencies
============

* `Custom Actions API <mistral-custom-actions-api.html>`_


Testing
=======

This will reduce the testing burden on the main Mistral repository. However,
additional test cases will be needed for mistral-extra. It may also be wise to
setup a periodic test to verify that a recent version of Mistral master still
works with mistral-extra.


References
==========

None
