..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================================
Support connection to arbitrary Openstack clouds
================================================

https://blueprints.launchpad.net/mistral/+spec/mistral-multi-vim-support


Problem description
===================

Mistral is configured to execute workflows on a specific cloud (VIM (Virtual
Infrastructure Manager) in ETSI MANO terms). In order to execute workflows on a
different cloud one needs to start a new Mistral instance with the cloud
specific configuration. When Mistral is used in standalone mode, this is an
undesired overhead and can cause unpredictable resource usage patterns.

This blueprint proposes to extend the workflow execution parameters to make it
possible to target a specific cloud without modifying the configuration of the
Mistral service.


Use Cases
---------

* As a tenant, I want to execute the same workflow on different clouds without
  having to start a new Mistral instance with changed configuration.


Proposed change
===============

Both the Mistral server and command line client are affected.

The 'execution-create' functionality should take parameters that describe the
target cloud for the execution. The following optional parameters should be
added:

- target_auth_url: auth URL of the target cloud
- target_auth_token: valid authentication token for the target cloud
- target_ca_cert: CA cert of target cloud

If both present, these are used to execute the workflow actions. If none are
present, then the current legacy operation mode is used, and the preconfigured
authetication URL is used in the actions. In any other case the execution
creation should fail.

These parameters are stored in the context field of the execution.

The parameters are added as headers to the HTTP API request.

The self authentication of Mistral should be carried out the same way as done
currently.

Cron triggers need the admin credentials for the tartget cloud. We do not
consider this case in the current proposal.

Alternatives
------------

* Start mulitple Mistral instances with different settings.
* This is an inflexible solution for the problem and the setup of the new
instances incurs significant administrative overhead.


Data model impact
-----------------

The change affects the `context` information of the execution object by
including the target auth URL and target token. The context is stored as Json,
so this change should not require DB migration.


REST API impact
---------------

*POST /executions*

This method should now accept the new optional target_* parameters according
to the specified rules.

Output should not change.


End user impact
---------------

The python-mistralclient should accept the following parameters:

- TARGET_OS_USERNAME: user name on the target cloud
- TARGET_OS_PASSWORD: password on the target cloud
- TARGET_OS_TENANT: tenant on the target cloud
- TARGET_OS_AUTH_URL: keystone URL of the target cloud
- TARGET_OS_CA_CERT: CA cert of target cloud

The client should authenticate both towards the OS_AUTH_URL and
TARGET_OS_AUTH_URL keystones.

Either all or none of these parameters should be set.


Performance Impact
------------------

None.


Deployer impact
---------------

This change takes effect immediately after deployment.


Implementation
==============

Assignee(s)
-----------

Primary assignee:

Other contributors:


Work Items
----------

* Implement the changes in the python-mistralclient

  * Add support for taking new parameters from environment and command line


* Implement the changes in Mistral

  * Inject auth URI in execution context
    * Reason: Actions require the target Auth URI
    * Tasks:
      * Set auth_uri in context either from the TARGET_OS_AUTH_URL header or
        from CONF.

  * Eliminate admin user for Keystone
    * Reason: Admin credentials should not be required to connect to target
      cloud.
    * Tasks:
      * Use non-admin Keystone client
      * Use 'tokens' API to retrieve service endpoints

  * Use auth URL from context to create service clients
    * Reason: service clients need to connect to target cloud
    * Task:
      * Do as stated above

  * Add new headers to allowed_headers
    * Reason: this feature may be used in the future


Dependencies
============

None.


Testing
=======

* Execute a Mistral workflow with targeting a different cloud than what is
  declared in the configuration.
* Create two simultaneously ran executions of
  the same mistral workflow targeting different clouds/regions/tenants. Check
  if both succeed.


References
==========

None.
