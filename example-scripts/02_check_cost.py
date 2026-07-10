"""Check the price of a request before spending anything.

Adding "check_cost": true runs a FREE dry run: the API returns the exact price
and generates nothing. Great for budgeting automated workflows before committing.

    python 02_check_cost.py
"""
from rd_client import check_cost, generate, get_balance, save_images

payload = {
    "prompt": "A knight resting by a campfire in a forest clearing at night",
    "prompt_style": "rd_pro__default",
    "width": 256,
    "height": 256,
    "num_images": 2,
}

price = check_cost(payload)  # free — nothing is generated or charged
balance = get_balance()
print(f"This request would cost ${price:.3f}. Your balance is ${balance:.3f}.")

if price <= balance:
    result = generate(payload)
    print(f"Generated {save_images(result, 'output_cost_checked')}")
    print(f"Charged ${result['balance_cost']}, ${result['remaining_balance']} remaining.")
else:
    print("Not enough balance — top up at https://www.retrodiffusion.ai/app/balance")
