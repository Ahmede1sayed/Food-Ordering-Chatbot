@router.post("/cart/add")
def add_to_cart(request: CartRequest, db: Session = Depends(get_db)):
    total = calculate_total(db, request.items)

    return {
        "items": request.items,
        "total_price": total
    }
