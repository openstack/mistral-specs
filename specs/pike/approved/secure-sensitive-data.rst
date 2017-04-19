..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=======================
Securing Sensitive Data
=======================

Launchpad blueprint:

https://blueprints.launchpad.net/mistral/+spec/mistral-secure-sensitive-data

This specification describes additions/changes to the DSL to allow a workflow
author to describe fields that should be treated as sensitive. By marking
a field as sensitive, it will signal that the engine should redact said
field from logs.

Additionally, a decarator will be made available to Action developers to mark
parameters as secret, thus treating them in a sensitive way.

Problem description
===================

Currently, there is no regard for sensitive data when writing information to
logs, and other places, mainly because Mistral is agnostic to the values
passed to it. It cannot currently distinguish sensitive data from "normal"
data. In order for Mistral to make this distinction, some additions to the DSL
must be made in order to signify data that is sensitive, and should be
redacted.

Use Cases
---------

Hiding passwords from logs
^^^^^^^^^^^^^^^^^^^^^^^^^^
As a workflow author, I want to have a password as input, and when Mistral
logs information about my workflow, I do not want the password to be in
plain text. It should be displayed as '*********'.

Proposed change
===============

Add a 'hidden' section to the workflow DSL. One can use a regex to specify a
pattern of values to hide.
Add a decorator to be used when developing custom actions.
Create a special data type, for example class Hidden, with string
representation "******" so that if something is wrapped into it we'll never
see it in logs in its initial form.
Store Hidden instances in encoded form in DB, decode them when fetched
from DB.


.. code-block:: yaml

  ---
  version: "2.0"
  wf:
    input:
      - username
    hidden:
      - keyA
      - secret_*
    tasks:
      taskA:
        action: my_action
        publish:
          keyA: <% task(taskA).result.foobar %>
          secret_value: <% task(taskA).result.baz %>
        on-success:
          - taskB
      taskB:
        action: my_action2
        input:
          arg1: <% $.keyA %>
          secret_value: <% $.secret_value %>

Note: arg1 will now be in the clear. If desired, arg1 would need to be added
to the 'hidden' list.


An example for actions:

.. code-block:: python

  from mistral_lib.secret import protect

  @hidden(['password'])
  class MyAction(Action):
      
      def init(self, password):
          # do something

Alternatives
------------

Alternatively, we could specify a hidden property at the task level. Nothing
in the spec precludes this in the future.

.. code-block:: yaml

  tasks:
    taskA:
      action: my_action
      hidden:
        - password
      input:
        password: <%...%>

One could also use a yaql expression. There was not much support for this
approach.

.. code-block:: yaml

  tasks:
    taskA:
      action: my_action
      input:
        username: <% ... %>
        password: $.secret(<% ... %>)

Another option would be to extend the syntax of the workflow input section:

.. code-block:: yaml

  ---
  version: "2.0"
  wf:
    input:
      username: ""
      password:
        hidden: true


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

Can use the decorator to mark sensitive inputs.

Workflow developers
^^^^^^^^^^^^^^^^^^^

Can use the 'secret' section to signify sensitive fields.

Performance Impact
------------------

No significant impact is expected. Minor is possible.

Deployer impact
---------------

None.

Implementation
==============

Assignee(s)
-----------

Brad P. Crochet <brad@redhat.com>, IRC: thrash

Secondary
^^^^^^^^^

Dougal Matthews <dougal@redhat.com>, IRC: d0ugal

Work Items
----------

* Implement new section 'hidden' in workflow DSL
* Implement new decorator for custom actions
* Store 'hidden' data to DB in some type of encoded form, or perhaps just
  masked.

Dependencies
============

No additional dependencies are required.

Testing
=======

The action decorator can be tested via unit tests.
The workflow DSL additions will likely need to be tested on devstack via
tempest.

References
==========

Launchpad bug:
https://bugs.launchpad.net/mistral/+bug/1337268
