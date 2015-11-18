========================================
OpenStack Workflow Engine Specifications
========================================

This git repository is used to hold approved design specifications for Mistral
project. Reviews of the specs are done in gerrit, using a similar workflow to
how we review and merge changes to the code itself.

This would apply to new blueprints proposed in Mistral project from Mitaka,
this new process provides a way to fast-track the feature history of Mistral,
which is very useful for new comers to learn how Mistral evolves, where we
are, and where we're going.

First, create a blueprint in launchpad and populate it with your spec's
heading. Then, propose a spec following the template which can be found at
``specs/template.rst``. This will be given an initial, high-level review to
determine whether it is in scope and in alignment with project direction,
which will be reflected on the review comments. If the spec is approved, you
can continue with your code implementation, and update launchpad to set the
specification URL to the spec's location on::

    https://specs.openstack.org/openstack/mistral-specs/

The Mistral PTL(or someone else on behalf of him) will update the release
target, priority, and status accordingly.

If a specification has been approved but not completed within one or more
releases since the approval, it may be re-reviewed to make sure it still makes
sense as written. Specifications are proposed by adding them to the
``specs/<cycle>/approved`` directory and posting it for review. When a spec is
fully implemented, it should be moved to ``specs/<cycle>/implemented``.

You are welcome to submit patches associated with a blueprint, whose
specification may have not been approved, but they will have a -2 ("do not
merge") until the specification has been approved. This is to ensure that the
patches don't get accidentally merged beforehand. You will still be able to
get reviewer feedback and push new patch sets, even with a -2.
