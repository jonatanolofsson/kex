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
