Django AJAX Changelist
===============================

*NOTE: this project is currently untested, lacks detailed documentation, and has only been used in production for a limited SelectField use case.  The goal of the project is to support inline editing of all field types (using their corresponding widgets) from the Django admin changelist view.*

This project extends Django ModelAdmin to support editing specified fields directly from the changelist (the Django admin's listview of objects of a given Model).

AJAX editing of fields from the changelist is useful when you need to quickly change a few properties of objects in the changelist -- instead of clicking through to each object's page, saving, and returning to the list, you can make the edits right from the list.

Usage
---------

```python
class BearAdmin(AjaxModelAdmin):
  form = BearForm  # usual form you'd use for your ModelAdmin here, nothing special needed

  # Specify the fields you'd like to be able to edit via AJAX here:
  ajax_fields = ('snout_length', 'honey_affinity_score',)
  
  # Specify the remainder of the fields you'd like to show in the changelist view:
  list_display = ('name', 'is_fictional',)
```

Form field/widget display approach
--------------------------------------

To take advantage of Django's form widgets, widgets are rendered on the serverside.  Currently they are rendered inline in the changelist view, though retrieving via AJAX would be more efficient for some field types.

Known Issues
-----------------

* jQuery 1.9.1 is added without namespacing and calling noConflict()
* Use in conjunction with ManyToManyFields:
    * Without extra user intervention (prefetching and caching options list), rendering a Select or similar widget for a M2M field generates a ton of extra queries when loading the changelist view.
    * Select widgets with many options will weigh down the admin page. (In future this can be handled by retrieving them via AJAX when a field is selected)
* Doesn't work with django-taggit fields and likely many other third-party provided fields/their corresponding widgets.
* The form fade-in/fade-out animations are potentially quite annoying; a switch should be provided to disable them.
