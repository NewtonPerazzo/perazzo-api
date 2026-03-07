from slugify import slugify


def generate_unique_slug(name: str, exists_callback):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1

    while exists_callback(slug):
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug