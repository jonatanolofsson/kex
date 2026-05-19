Annotation contract
===================

Apps register themselves on the kex landing page by adding ``kex/*``
annotations to their ArgoCD ``Application`` CR. The CR lives in
whichever repo owns the app's deployment; no central catalog edit
required.

Required
--------

``kex/enabled``: ``"true"``
    Visibility gate. Omit or set to ``"false"`` to hide.

Display
-------

``kex/title``
    Human-readable name shown on the card.
``kex/description``
    One-line summary on the card.
``kex/group``
    Section heading the card is sorted into.
``kex/icon``
    Icon hint (string keyword; mapped to an icon in the UI).

Display ordering
----------------

Two independent axes, both float-valued and defaulting to ``0``; both
silently fall back to the default on malformed values so a typo can't
crash the index.

Group order — ``kex/groupweight``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Controls **between**-group ordering. A group's effective rank is
    the **min** of its apps' ``kex/groupweight``, so any single app
    can pull its group up — there's no central registry, and apps
    that don't care stay quiet at ``0``. Lower number = higher on
    the page.

    Conventions used across the EdgeLab cluster today:

    - ``-30`` — operator-critical edge apps (Converter IR, Truckbed).
    - ``-20`` — actively-developed ML platform anchors (Flyte).
    - ``-10`` — LLM stack (llm-edgelab).
    - ``0`` — default; Data and Storage, DevOps, Platform.
    - ``+10`` — background infrastructure (cert-manager, reloader,
      network-check, …) that should sink to the bottom.

    Ties break on group name via ``localeCompare``.

Within-group order — ``kex/weight``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Controls **within**-group ordering. Each app's value places it
    among the cards inside its group; lower number = earlier in the
    row. Apps that don't care stay at ``0`` and alphabetise on
    title (then ``name``).

    Conventions used today:

    - ``-10`` — "first card in group" anchor. Platform Docs uses
      this so operators landing on the page see the docs entry first
      within DevOps.
    - ``0`` — default.

    The two axes are **independent**: declaring ``kex/weight: -10``
    does **not** affect group order. To also float the group, set
    ``kex/groupweight`` separately.

Migration from v1.1
~~~~~~~~~~~~~~~~~~~

    Before v1.2 there was a single ``kex/weight`` annotation that
    controlled group order. To free up the natural name for the new
    within-group axis, the v1.1 ``kex/weight`` semantics moved to
    ``kex/groupweight``. Magnitudes didn't change; rename the key
    only.

Detail page
-----------

``kex/about``
    Long-form markdown rendered on the detail page.
``kex/links.<key>``
    Free-form sidebar links. The suffix becomes the button label.
    Example: ``kex/links.docs: https://...``.

Git scoping (v2-reserved)
-------------------------

``kex/git.path``
    Monorepo subdirectory to scope contributors data. Defaults to the
    Application's ``spec.source.path``. Reserved for v2.

Visibility (v2-reserved)
------------------------

``kex/visibility.groups``
    Comma-separated list of AD groups allowed to see this app.
    Reserved for v2; v1 ignores it.
