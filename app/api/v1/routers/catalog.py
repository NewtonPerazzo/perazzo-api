import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cart import CartCreate, CartProductsReplace
from app.schemas.catalog import (
    CatalogCartCheckoutRequest,
    CatalogCartPreviewTotalRequest,
    CatalogCartPreviewTotalResponse,
    CatalogCartResponse,
    CatalogCategoryResponse,
    CatalogHomeResponse,
    CatalogHomeSectionResponse,
    CatalogProductPageResponse,
    CatalogProductResponse,
    CatalogProductsPageResponse,
    CatalogStoreResponse,
)
from app.schemas.order import OrderCreate, OrderResponse, ProductOrderCreate
from app.schemas.payment_method import PaymentMethodResponse
from app.schemas.delivery_method import DeliveryMethodResponse
from app.services.cart import CartService
from app.services.category import CategoryService
from app.services.delivery_method import DeliveryMethodService
from app.services.order import OrderService
from app.services.payment_method import PaymentMethodService
from app.services.product import ProductService
from app.services.store import StoreService
from app.util.store_hours import is_open_now, normalize_business_hours

router = APIRouter(prefix="/catalog", tags=["Catalog"])

OTHERS_CATEGORY_ID = "others"
OTHERS_CATEGORY_SLUG = "others"
OTHERS_CATEGORY_NAME = "Outros"


def _get_active_store_or_404(store_slug: str, db: Session):
    store = StoreService(db).get_by_slug(store_slug)
    if not store or not store.has_catalog_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found")
    return store


def _serialize_store(store) -> CatalogStoreResponse:
    return CatalogStoreResponse(
        id=store.id,
        name=store.name,
        slug=store.slug,
        description=store.description,
        phone=store.phone,
        whatsapp=store.whatsapp,
        address=store.address,
        instagram=store.instagram,
        email=store.email,
        logo=store.logo,
        color=store.color,
        is_accepted_send_order_to_whatsapp=store.is_accepted_send_order_to_whatsapp,
        business_hours=normalize_business_hours(store.business_hours),
        is_open_now=is_open_now(store.business_hours),
    )


def _ensure_store_open_for_cart_actions(store, db: Session):
    service = StoreService(db)
    if not service.is_open_now(store):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store is currently closed")


def _serialize_product(product) -> CatalogProductResponse:
    return CatalogProductResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        price=float(product.price),
        description=product.description,
        stock=product.stock,
        image_url=product.image_url,
    )


def _serialize_category(category, products_count: int) -> CatalogCategoryResponse:
    return CatalogCategoryResponse(
        id=str(category.id),
        name=category.name,
        slug=category.slug,
        description=category.description,
        products_count=products_count,
    )


def _others_category(products_count: int) -> CatalogCategoryResponse:
    return CatalogCategoryResponse(
        id=OTHERS_CATEGORY_ID,
        name=OTHERS_CATEGORY_NAME,
        slug=OTHERS_CATEGORY_SLUG,
        description=None,
        products_count=products_count,
    )


def _serialize_cart(cart: dict) -> CatalogCartResponse:
    cart_products = []
    for item in cart.get("products", []):
        raw_product = item.get("product")
        product = _serialize_product(raw_product)
        cart_products.append(
            {
                "product": product,
                "amount": int(item.get("amount", 0)),
                "price": float(item.get("price", 0.0)),
            }
        )

    customer_data = None
    raw_customer = cart.get("customer")
    if raw_customer:
        first_name, _, tail = str(raw_customer.get("name", "")).partition(" ")
        customer_data = {
            "first_name": first_name,
            "last_name": tail,
            "whatsapp": raw_customer.get("phone", ""),
            "address": raw_customer.get("address"),
            "neighborhood": raw_customer.get("neighborhood"),
        }

    return CatalogCartResponse(
        id=cart["id"],
        products=cart_products,
        customer=customer_data,
        is_to_deliver=cart.get("is_to_deliver"),
        delivery_method_id=cart.get("delivery_method_id"),
        payment_method_id=cart.get("payment_method_id"),
        observation=cart.get("observation"),
        total_price=float(cart["total_price"]),
        created_at=cart["created_at"],
        updated_at=cart["updated_at"],
    )


def _build_categories_payload(product_service: ProductService, categories: list, search: str | None):
    payload: list[tuple[object, CatalogCategoryResponse]] = []
    for category in categories:
        count = product_service.count(search=search, category_id=category.id, catalog_mode=True)
        if count <= 0:
            continue
        payload.append((category, _serialize_category(category, products_count=count)))

    uncategorized_count = product_service.count(search=search, uncategorized=True, catalog_mode=True)
    if uncategorized_count > 0:
        payload.append((None, _others_category(products_count=uncategorized_count)))

    return payload


@router.get("/{store_slug}/home", response_model=CatalogHomeResponse)
def get_catalog_home(
    store_slug: str,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)

    category_service = CategoryService(db)
    product_service = ProductService(db)

    categories = category_service.list(skip=0, limit=200)
    categories_with_payload = _build_categories_payload(product_service, categories, search)
    categories_payload = [item[1] for item in categories_with_payload]

    sections: list[CatalogHomeSectionResponse] = []
    for category, category_payload in categories_with_payload:
        if category is None:
            continue
        products = product_service.list(
            skip=0,
            limit=20,
            search=search,
            category_id=category.id,
            catalog_mode=True,
        )

        if len(products) == 0:
            continue

        sections.append(
            CatalogHomeSectionResponse(
                category=category_payload,
                products=[_serialize_product(product) for product in products],
            )
        )

    uncategorized_products = product_service.list(skip=0, limit=20, search=search, uncategorized=True, catalog_mode=True)
    if len(uncategorized_products) > 0:
        sections.append(
            CatalogHomeSectionResponse(
                category=_others_category(products_count=len(uncategorized_products)),
                products=[_serialize_product(product) for product in uncategorized_products],
            )
        )

    return CatalogHomeResponse(
        store=_serialize_store(store),
        categories=categories_payload,
        sections=sections,
    )


@router.get("/{store_slug}/products", response_model=CatalogProductsPageResponse)
def list_catalog_products(
    store_slug: str,
    search: str | None = None,
    category_slug: str | None = None,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)

    category_service = CategoryService(db)
    product_service = ProductService(db)

    categories = category_service.list(skip=0, limit=200)
    categories_with_payload = _build_categories_payload(product_service, categories, search)
    categories_payload = [item[1] for item in categories_with_payload]

    selected_category = None
    category_id: uuid.UUID | None = None
    uncategorized = False

    if category_slug:
        if category_slug == OTHERS_CATEGORY_SLUG:
            uncategorized = True
            uncategorized_count = product_service.count(search=search, uncategorized=True)
            selected_category = _others_category(products_count=uncategorized_count)
        else:
            category = category_service.get_by_slug(category_slug)
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

            category_id = category.id
            count = product_service.count(search=search, category_id=category.id, catalog_mode=True)
            selected_category = _serialize_category(
                category,
                products_count=count,
            )

    products = product_service.list(
        skip=0,
        limit=200,
        search=search,
        category_id=category_id,
        uncategorized=uncategorized,
        catalog_mode=True,
    )

    return CatalogProductsPageResponse(
        store=_serialize_store(store),
        categories=categories_payload,
        selected_category=selected_category,
        products=[_serialize_product(product) for product in products],
    )


@router.get("/{store_slug}/products/{product_slug}", response_model=CatalogProductPageResponse)
def get_catalog_product(
    store_slug: str,
    product_slug: str,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)

    product_service = ProductService(db)
    product = product_service.get_by_slug(product_slug)
    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return CatalogProductPageResponse(
        store=_serialize_store(store),
        product=_serialize_product(product),
    )


@router.get("/{store_slug}/categories/{category_slug}", response_model=CatalogProductsPageResponse)
def get_catalog_category_products(
    store_slug: str,
    category_slug: str,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return list_catalog_products(
        store_slug=store_slug,
        search=search,
        category_slug=category_slug,
        db=db,
    )


@router.get("/{store_slug}/payment-methods", response_model=list[PaymentMethodResponse])
def list_catalog_payment_methods(
    store_slug: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    _get_active_store_or_404(store_slug, db)
    return PaymentMethodService(db).list(skip=skip, limit=limit)


@router.get("/{store_slug}/delivery-methods", response_model=list[DeliveryMethodResponse])
def list_catalog_delivery_methods(
    store_slug: str,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    _get_active_store_or_404(store_slug, db)
    return DeliveryMethodService(db).list(skip=skip, limit=limit)


@router.post("/{store_slug}/carts", response_model=CatalogCartResponse, status_code=status.HTTP_201_CREATED)
def create_catalog_cart(
    store_slug: str,
    data: CartCreate,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)
    _ensure_store_open_for_cart_actions(store, db)
    cart = CartService(db).create(data)
    return _serialize_cart(CartService(db).serialize(cart))


@router.get("/{store_slug}/carts/{cart_id}", response_model=CatalogCartResponse)
def get_catalog_cart(
    store_slug: str,
    cart_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    _get_active_store_or_404(store_slug, db)

    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    return _serialize_cart(service.serialize(cart))


@router.put("/{store_slug}/carts/{cart_id}/products", response_model=CatalogCartResponse)
def replace_catalog_cart_products(
    store_slug: str,
    cart_id: uuid.UUID,
    data: CartProductsReplace,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)
    _ensure_store_open_for_cart_actions(store, db)

    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    updated = service.replace_products(cart, data.products)
    if updated is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return _serialize_cart(service.serialize(updated))


@router.post("/{store_slug}/carts/{cart_id}/preview-total", response_model=CatalogCartPreviewTotalResponse)
def preview_catalog_cart_total(
    store_slug: str,
    cart_id: uuid.UUID,
    data: CatalogCartPreviewTotalRequest,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)
    _ensure_store_open_for_cart_actions(store, db)

    cart_service = CartService(db)
    cart = cart_service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    products = [ProductOrderCreate(product_id=item.product_id, amount=item.amount) for item in cart.items]
    total = OrderService(db).preview_total_with_delivery(
        products=products,
        is_to_deliver=data.is_to_deliver,
        delivery_method_id=data.delivery_method_id,
    )
    return {"total_price": total}


@router.post("/{store_slug}/carts/{cart_id}/checkout", response_model=OrderResponse)
def checkout_catalog_cart(
    store_slug: str,
    cart_id: uuid.UUID,
    data: CatalogCartCheckoutRequest,
    db: Session = Depends(get_db),
):
    store = _get_active_store_or_404(store_slug, db)
    _ensure_store_open_for_cart_actions(store, db)

    cart_service = CartService(db)
    cart = cart_service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    if not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart has no products")

    if data.is_to_deliver and not data.delivery_method_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery method is required")

    if data.is_to_deliver and not data.customer.address:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Address is required for delivery")

    payment_method = PaymentMethodService(db).get_by_id(data.payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment method not found")

    full_name = f"{data.customer.first_name.strip()} {data.customer.last_name.strip()}".strip()

    order_payload = OrderCreate(
        products=[
            ProductOrderCreate(product_id=item.product_id, amount=item.amount)
            for item in cart.items
        ],
        customer={
            "name": full_name,
            "phone": data.customer.whatsapp,
            "address": data.customer.address,
            "neighborhood": data.customer.neighborhood,
        },
        is_to_deliver=data.is_to_deliver,
        delivery_method_id=data.delivery_method_id,
        payment_method=payment_method.name,
        observation=data.observation,
    )

    order_service = OrderService(db)
    order = order_service.create(data=order_payload)
    response = order_service.serialize(order)

    cart_service.delete(cart)

    return response


@router.delete("/{store_slug}/carts/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_cart(
    store_slug: str,
    cart_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    _get_active_store_or_404(store_slug, db)

    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    service.delete(cart)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
