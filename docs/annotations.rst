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

``kex/weight``
    Float (default ``0``). Lower values float the app's group higher on
    the landing page. The group's effective rank is the **min** of its
    apps' weights, so any single app can pull its group up — there's no
    central registry, and apps that don't care stay quiet at ``0``.

    Conventions used across the EdgeLab cluster today:

    - ``-30`` — operator-critical edge apps (Converter IR, Truckbed).
    - ``-20`` — actively-developed ML platform anchors (Flyte).
    - ``-10`` — LLM stack (llm-edgelab).
    - ``0`` — default; Data and Storage, DevOps, Platform.
    - ``+10`` — background infrastructure (cert-manager, reloader,
      network-check, …) that should sink to the bottom.

    Ties (apps with identical group weights) break on group name via
    ``localeCompare`` for deterministic order across reloads. Malformed
    values fall back silently to ``0``.

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
