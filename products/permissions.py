"""
Permission utilities for products app.
"""

def is_admin_or_staff(user):
    """Check if user is admin or staff member."""
    return user.is_authenticated and (user.is_admin or user.is_staff_member)


def can_view_products(user):
    """Check if user can view products."""
    return user.is_authenticated


def can_edit_products(user):
    """Check if user can edit products."""
    return is_admin_or_staff(user)


def can_delete_products(user):
    """Check if user can delete products."""
    return user.is_authenticated and user.is_admin
