..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Custom Context for Executions
==========================================

https://blueprints.launchpad.net/mistral/+spec/mistral-custom-context-for-executions

Currently it is not possible to send contextual parameters to actions. The
context contains only the OS auth parmeters in the SecurityContext and some
details about the execution in the ExecutionContext. There is general demand
to be able to pass parameters at this level to make these pervasively present
throughout the execution without contaminating the workflow definition.


Problem description
===================

Use Cases
---------

1. Pass context parameters to custom actions

Custom actions may need various contextual parameters, e.g. request/correlation
IDs, authentication tokens, miscellaneous data. These pieces of data should not
be passed as parameters to avoid getting logged and to be able to access them
in any part of the execution.

2. Provide auth parameters for OpenStack actions

Currently the OpenStack actions use the SecurityContext to get the authentication
data. The X-Target-* headers provide an alternative way to override these
parameters but the size of these headers is limited and already makes them
unable to handle larger OpenStack installations. [1,2]

3. Clearly separate the Mistral API authentication parameters from the
OpenStack Action authentication parameters

The Mistral API has different plugins for authentication: Keystone and Keycloak
at the time of writing this specification. OpenStack actions should not rely
on the parameters used for the Mistral API authentication as this tight
coupling introduces unwanted restrictions. E.g. it is fairly awkward to
use Keycloak authentication and run OpenStack actions in the same execution.

This separation also helps the efforts to separate OpenStack actions from
the Mistral Core.


Proposed change
===============

Add custom_context dict to the execution type API resources (Execution,
ActionExecution) and use the data in it to update the context.

The 'os.auth' key is used to store the X-Target-* headers data in its
current format. To decrease the size of the final context, this key
is removed from the custom_context after processing.

Other keys can be used freely by custom action implmementations. These
are stored under the 'custom_context' key.


Alternatives
------------

1. Keep using the X-Target-* headers: there are already bugs filed

2. Send this info hidden in the request body
E.g. we could add custom_context to the POST request body and we could
add it to the context in the ContextHook. However, the request body is
present only in text form in the ContextHook and the parameter cannot
be left in the request body as it causes the WSME implementation to
fail unmarshalling the input objects.

Data model impact
-----------------

Not affected.

REST API impact
---------------

Add the custom_context dict field to the Execution and ActionExecution
API resources.

Does not involve REST API modification.

End user impact
---------------

mistral exection-create
~~~~~~~~~~~~~~~~~~~~~~~

Add the --custom_context parameter.

    mistral execution-create --custom_context='{"correlation_id":"1212ddaa33"}' ...

mistral run-action
~~~~~~~~~~~~~~~~~~

Add the --custom_context parameter.

    mistral run-action --custom_context='{"correlation_id":"1212ddaa33"}' ...


Performance impact
------------------

Large custom_contexts can slow down the execution of workflows as it is
passed in the RPC messages and saved in the delayed_calls table. For the
same reason, this can affect the memory usage of components.


Backward compatibility
----------------------

The clients sending the custom_context parameter will not be able to
use the execution-create and run-action APIs with previous Mistral API
instances because the resource unmarshalling step will fail.


Deployer impact
---------------

None.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  akovi

Other contributors:

Work Items
----------

Add the --custom_context parameter to the mistral run-action command

Add the --custom_context parameter to the mistral create-exection command

Add the custom_context field to the Execution API resource

Add the custom_context field to the ActionExecution API resource

Add the support for the special 'os.auth' key (client and API)

Add the custom_context to mistral-lib


Testing
=======

API test to ensure the correct parameter handling in Execution and ActionExecution

Check that the custom parameters are loaded in context.custom_context


References
==========


[1] https://bugs.launchpad.net/python-mistralclient/+bug/1702324
[2] https://bugs.launchpad.net/mistral/+bug/1699248
