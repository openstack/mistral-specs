..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================
Mistral HA and Scalability
==========================

Launchpad blueprints:

https://blueprints.launchpad.net/mistral/+spec/mistral-ha-spec
https://blueprints.launchpad.net/mistral/+spec/mistral-ha-gate
https://blueprints.launchpad.net/mistral/+spec/mistral-multinode-tests
https://blueprints.launchpad.net/mistral/+spec/mistral-fault-tolerance
https://blueprints.launchpad.net/mistral/+spec/mistral-scale-up-down

Mistral needs to be highly available (HA) and scalable.

This specification doesn't attempt to describe all steps and measures that
need to be taken in order to achieve these goals. It rather aims to set a
common ground for understanding what tasks and challenges the team needs to
solve and proposes approximate approaches for that.

Problem description
===================

In a nutshell, being highly available and scalable means that we should
be able to run more than one Mistral cluster component of any type (api,
engine, executor) and gain more reliability and performance.
Originally, Mistral was designed to be fully asynchronous and thus easily
scalable, so we know that Mistral, in fact, works with multiple APIs, engines
and executors and its performance becomes higher in this case.
High availability though is a complex non functional requirement that is
usually achieved by making lots of changes to account for various failure
situations that can happen with multiple nodes of the systems. Particularly,
the system should gracefully handle cluster topology changes: node addition
and node departure. These events should not affect normal work of workflows
that have already been started.
So far, the Mistral team hasn't spent significant time on HA. Although Mistral
partially implements these two non functional requirements we need to make
sure that all of their corresponding aspects are implemented and tested. This
specification aims to clearly define these aspects and roughly propose
approaches for taking care of them.

Use Cases
---------

* Scalability is needed when performance of a Mistral cluster component,
  such as Mistral engine, limited by resources (I/O, RAM, CPU) of a single
  machine, is not sufficient. Those are any use cases that assume significant
  load on Mistral, essentially lots of tasks processed by Mistral per time
  unit.
  Example: hosted workflow service in a public cloud.
* High availability is critically important for use cases where workflows
  managed by Mistral should live even in case of infrastructure failures.
  To deal with these failures the system needs to have redundancy, i.e.
  extra instances of cluster components. Losing part of them doesn't affect
  normal work of the system, all functionality continues to be accessible.



Proposed change
===============

**Testing infrastructure**

Currently, Mistral team doesn't have any infrastructure that would allow to
automate testing of multi-node Mistral, whether we want to test scalability
properties or reliability and availability. The first step towards achieving
the goals defined by the spec is to create such an infrastructure.

Currently, the requirements for this infrastructure are seen as follows:

* New gate in OpenStack CI that will allow to run any number of Mistral
  cluster components as separate processes
* Python utility methods that will allow to start, stop and find running
  Mistral cluster components. This is required because we should be able to
  have different number of cluster components for different tests within the
  same gate. It will also allow to test addition and departure of cluster
  nodes (scale up and down).
* Means that will allow to imitate infrastructure failures. One of the most
  important is lost messages in RPC.
* A tool for benchmarking Mistral performance when it's installed in multi-node
  mode. Ideally, it needs to be a separate gate (most likely based on Rally)


**Mistral stable multi-node topology**

This work item mostly assumes testing Mistral with multiple nodes when the
number of node is stable. The most important part is to test multiple engines
because engine is the part of the system that creates complex database
transactions and there used to be known issues related to that like deadlocks.
These known issues seem to have been fixed but we need to create test harness
for this and make sure it's tested automatically on every commit. Potentially,
we might still have some issues like that.

**Mistral variable multi-node topology (scale up/down)**

Once multi-node Mistral is tested with a stable cluster topology we need to
make sure to create tests where nodes are added and removed while workflows
are running. These workflows must finish successfully regardless of cluster
topology changes, only if there's at least one running component of every
type (engine, executor, api).
In this part we expect issues related to lost RPC messages for communications
where message acknowledgements are not used. It's possible that component A
will send a message component B, and if component B polls the message from
a message queue and goes down before the message is fully processed and
result is sent back, then state of a corresponding object in the database
won't be updated (action execution, task execution, workflow execution).
Having that said, as of now, there's no opportunity to fix this when using
oslo.messaging based RPC implementation because it doesn't support message
acknowledgement needed for the "Work queue" pattern, i.e. "at-least-once"
delivery. See https://www.rabbitmq.com/tutorials/tutorial-two-python.html for
details. For now, we have to use Kombu-based Mistral RPC which supports this
mechanism. However, it's known that message acknowledgements should be used
in more cases where the mistral services communicate, than currently enabled.
For example, it is enabled on the executor side so that a message sent to an
executor (to run an action) is acknowledged after it's fully processed. But
it's known that it's not enabled on the engine side when, for example,
executor sends a result of the action back to Mistral. Part of this work
item will be identifying all such gaps in the Mistral communication protocol
and fix them.
Another visible problem is graceful scale down, when the node that is
intentionally leaving the cluster should stop handling new incoming RPC
requests but complete requests that are already being processed. If this
concern is not taken care of, we'll be getting repeated message processing
problem, i.e. when in fact a message was processed more than once that in turn
leads to breaking normal logic of workflow processing. The example: an engine
sends a "run action" request to an executor, executor polls it, runs an action
and immediately after that goes down w/o having a chance to send the result
back to the engine acknowledging the initial message. So, in fact, the acton
already ran once. Then, since the message is not acknowledged, a message queue
broker will resend it to a different executor and it'll be processed again.
The solution: graceful shutdown when executor fully processes the message,
sends the result back, acknowledges the message and only then is allowed to
shut down. On this matter, we need to distinguish between idempotent and
non-idempotent actions. The described problem applies only to non-idempotent
actions since, from their definition, every execution of such action changes
the state of the system.

**Handling infrastructure failures**

Mistral should be able to gracefully handle the following infrastructure
outages:

* Temporary lost connectivity with the database
* Temporary lost connectivity with the message broker

Currently, there aren't automatic tests that would guarantee that Mistral
handles these situations gracefully w/o losing ability to complete workflows
that are already running. So this work stream assumes creating tests that
imitate these failures and fixing possible issues that may occur in this case.
The most important part is execution objects stuck in a non-terminal state
like RUNNING due to a temporary outage of the message broker or the database.
It is known that there can be situations when an RPC message is completely
lost. For example, RabbitMQ does not guarantee that if it accepted a message
it will be delivered to consumers. Automatic recovery looks impossible in this
case but we need to come up with approaches how to help operators identify
these situations and recover from them. This should be figured out during the
implementation phase.

**Benchmarking of multi-node Mistral**

We already have a CI gate based on Rally that allows benchmarking a single-node
Mistral. We need to create a gate and a tool set that will allow benchmarking
Mistral that has different number of nodes so that we see how scaling up/down
changes Mistral performance. When we're talking about Mistral performance,
until not explained, it's not clear what it means because if we mean workflow
execution time (from when it was started to when it was completed) then it
totally depends on what kind of workflow it is, whether it's highly parallel
or has only sequences, whether it has joins, "with-items" tasks, task policies
etc.
The proposal is to come up with several workflows that could be called
"reference workflows" and to measure execution time of these workflows in
seconds (minimal, average, highest) as well as "processing time per task" for
each one of them that would show how much time is needed to process an
individual task for all such workflows. These reference workflows together
should describe all kinds of elementary workflow blocks that any more complex
workflow can consist of. Thus these workflows will give us understanding about
performance of all most important workflow topologies. Plus we can have one or
more complex workflow built of these elementary blocks and measure its
execution time as well.

Currently, the proposed reference workflows are:

* Sequence of N tasks where each task is started only after the previous one.
  Without parallelism at all.
* N parallel tasks w/o connections between each other. Fully parallel workflow.
* X parallel sequences where each contains N tasks. Mixed sequential
  and parallel workflows.
* N parallel tasks joined by a task marked as "join: all"
* X parallel sequences where each contains N tasks joined by a task marked as
  "join: all"
* One task configured as "with-items" that processes N elements
* Complex workflow where all the previous items are combined together

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

Higher uptime of Mistral service (if by end user we mean those who call
Mistral API).

Performance Impact
------------------

* Performance of Mistral with more nodes will be higher than performance of
  Mistral with less nodes.

Deployer impact
---------------

Deployers will be able to run more Mistral nodes to increase performance and
redundancy/availability of the service.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  rakhmerov

Other contributors:
  melisha

Work Items
----------

* OpenStack CI job for testing Mistral in HA
* Make multi-node Mistral work reliably with a stable cluster topology
  (includes automatic testing)
* Make multi-node Mistral work reliably with a variable cluster topology
  (includes automatic testing)
* Make Mistral handle infrastructure failures
  (includes automatic testing)
* Fix known RPC communication issues (acknowledgements etc.)
* Create a set of automatic benchmarks (most likely with Rally) that will
  show how Mistral cluster scale up / scale down influence performance

Dependencies
============

None.


Testing
=======

* Use a new CI gate that will allow to run multiple cluster nodes and test
  how Mistral scales up and down and how it reacts on various infrastructure
  failures (more details above)

References
==========

None.
