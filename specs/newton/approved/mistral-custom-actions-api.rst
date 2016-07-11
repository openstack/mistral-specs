..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==================
Custom Actions API
==================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-custom-actions-api

This specification sets a formal basis for those Mistral users who want to
create their own actions and make them available to use as part of Mistral
workflows. The number one question that the spec addresses is "What is
available in Mistral code base in order to implement custom actions?"


Problem description
===================

Custom actions are now possible to create and it's as simple as just
implementing a class inherited from mistral.actions.base.Action that
has 3 methods:

* run() - executes main action logic, **mandatory** to implement

* test() - execute action in test mode, related to future dry-run
  functionality, optional to implement

* is_sync() - must return **True** if action returns its result right from
  method run() or **False** if method run() only starts action logic and
  result is supposed to be delivered later via public Mistral API

There's also a mechanism based on stevedore library that allows to plug in
new actions via adding new entry points in setup.cfg file.

If a custom action doesn't require any integration neither with Mistral
nor with OpenStack this is enough to know in order to implement it.

However, if this action needs to leverage more advanced capabilities
provided by Mistral and OpenStack then Action class itself doesn't
give any knowledge about means that can be used to achieve that.
A simple example of integration with OpenStack infrastructure is the need
to call endpoints of OpenStack services. In this case, at minimum, action
needs to be able to authenticate with Keystone, i.e., have access to
Mistral security context.

Use Cases
---------

Simple OpenStack actions
^^^^^^^^^^^^^^^^^^^^^^^^
As a user of Mistral I want to create actions that call OpenStack services.
In this case action needs to be able to access Mistral security context
that contains auth token to be able to pass it to a corresponding service.
Note: This use case is generally implemented within Mistral but it needs
to be rethought since OpenStack actions that are implemented now in Mistral
use Mistral Python code that is not assumed to be a public API and hence
stable.

Complex OpenStack actions
^^^^^^^^^^^^^^^^^^^^^^^^^
As a user of Mistral I want to create actions that call multiple OpenStack
services from within one action.

For example, we may want to create action
"create_cinder_volume_and_attach_to_vm" that creates a Cinder volume and
attaches it to a virtual instance. In this case action needs to have access
to Mistral security context that contains auth token so that it can pass
that token to Cinder and Nova.

Reusing existing actions
^^^^^^^^^^^^^^^^^^^^^^^^

As a user of Mistral I want to be able to reuse existing actions while
implementing my new actions so that I don't have to reimplement similar
functionality.

For example, I want to create action that checks if a certain virtual
instance exists in the tenant by calling Nova and if it does the action
runs a number of secure shell commands to configure it. In this scenario,
we need to call Nova and do ssh. Both already exist in Mistral as actions
"nova.servers_get" and "std.ssh". So there should be a mechanism allowing
to reuse those actions while creating a new more complex action.

Proposed change
===============

General idea
------------

We need to have one or more Python packages in Mistral that are designed
and documented as a public Python API for developers that want to create
custom actions. These packages should effectively provide a number of
classes that can be used directly or inherited as needed. They should
cover the following aspects of action development:

* Base class or a number of classes that can be extended in order to build
  new Mistral actions. Currently existing **mistral.actions.base.Action**
  is an example of such class.

* Module that provides access to security context associated with the
  current workflow that this action belongs to. Security context should
  at least include user, project/tenant, auth token.

* Module that provides access to current Mistral execution context. That
  context should include:

  * Current workflow execution id

  * Current task execution id

  * Current action execution id

* Package with most frequently used utils and data types used during
  custom actions development. For example, class
  mistral.workflow.utils.Result that now exists in the code base is
  needed by actions but it's not clear that it's part of Python API.

* Module that allows to get and reuse existing actions

Since these Python entities must be available for both engine and
executor they should be moved to a separate subproject of Mistral, for
example, **mistral-actions-api**.

Existing OpenStack actions should be moved out of mistral project into
a different Mistral subproject. The proposal is to use **mistral-extra**
repo for this purpose because although we use it only for collecting
Mistral examples its initial idea was also to have additional tools
and extensions in it.

Specific entities
-----------------

mistral.actions.api
^^^^^^^^^^^^^^^^^^^
Main Python package that contains all modules and classes which are part
of Custom Actions API.

mistral.actions.api.base
^^^^^^^^^^^^^^^^^^^^^^^^
Python module that contains base classes for custom actions. Currently
module **mistral.actions.base** performs similar function.

Note: Specific content of this module is out of scope of this spec and
must be defined at implementation stage.

mistral.actions.api.security
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Python module that contains required functions to get all required
information related to current OpenStack security context. At minimum:
user, project, auth token.

Note: Specific content of this module is out of scope of this spec and
must be defined at implementation stage.

mistral.actions.api.types
^^^^^^^^^^^^^^^^^^^^^^^^^
Python module that contains all data types that custom actions need to
use. One candidate to go to that module that now exists is
**mistral.workflow.utils.Result**.

Note: Specific content of this module is out of scope of this spec and
defined at implementation stage.

mistral.actions.api.utils
^^^^^^^^^^^^^^^^^^^^^^^^^
Python module that contains additional functions helpful for creating
new Mistral actions. At minimum: functions to get instances of existing
actions so that action developers could re-use functionality of existing
actions. Return type for these actions though must be rather a wrapper
that doesn't just call **Action.run()** method but instead uses Mistral
action execution machinery to actually call action just like as if it
was called as part of workflow (taking care of data transformations,
fulfilling security and execution context etc.)

Note: Specific content of this module is out of scope of this spec and
must be defined at implementation stage.

Alternatives
------------

None.

Data model impact
-----------------

None.

REST API impact
---------------

None.

End user impact
---------------

REST API users
^^^^^^^^^^^^^^
No impact.

Custom actions developers
^^^^^^^^^^^^^^^^^^^^^^^^^
Having to use Custom Actions API described in this spec whereas now they
can only use **mistral.actions.base** safely.

Performance Impact
------------------

No significant impact is expected. Minor is possible.

Deployer impact
---------------

Deployers will need to make sure to install a new library containing
Custom Action API packages, modules and classes. However, this impact
is not supposed to be severe because all dependencies must be handled
smoothly by Pip.

In case if there's an existing Mistral installation with installed
actions, some DB migration might be required. Changes in DB schema are
not expected though. If so, Mistral project should provide convenient
tools to help make this transition to using new actions.

Implementation
==============

Assignee(s)
-----------

To be found based on discussions around the spec.

Work Items
----------

* Create a new repo containing the code of Custom Actions API (e.g.
  **mistral-lib** or **mistral-common**, particular name is to be defined)
* Design and implement modules listed in Specific Entities section
* Provide deprecation mechanism so that during some period of time it
  would be possible to use the old approach for implementing Mistral
  actions (with **mistral.actions.base**) and the new one
* Fix existing action implementations so that they use new API
* Fix Mistral Executor accordingly
* Fix Mistral Engine accordingly
* Revisit and restructure repo **mistral-extra**
* Move existing OpenStack actions into **mistral-extra**


Dependencies
============

No additional dependencies are required.

Testing
=======

Custom Actions API can be tested on devstack based OpenStack CI gates
such as gate-mistral-devstack-dsvm by creating and running custom
actions that use this API.

References
==========

Initial patch for TripleO/Mistral integration:
https://review.openstack.org/#/c/282366/
