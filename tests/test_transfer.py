import asyncio
import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from decimal import Decimal

from app.main import app


@pytest.mark.asyncio
async def test_concurrent_transfers(tmp_path):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-API-Key": "devkey"}) as client:
        # create accounts
        r1 = await client.post("/accounts", json={"owner": "A", "initial_balance": 100.00})
        r2 = await client.post("/accounts", json={"owner": "B", "initial_balance": 0.00})
        a1 = r1.json()
        a2 = r2.json()

        # perform many concurrent transfers of $1 from A to B
        async def do_transfer():
            await client.post("/transfer", json={"from_id": a1["id"], "to_id": a2["id"], "amount": 1.00})

        tasks = [do_transfer() for _ in range(50)]
        await asyncio.gather(*tasks)

        r_final_a = await client.get(f"/accounts/{a1['id']}")
        r_final_b = await client.get(f"/accounts/{a2['id']}")
        bal_a = Decimal(str(r_final_a.json()["balance"]))
        bal_b = Decimal(str(r_final_b.json()["balance"]))

        assert bal_a + bal_b == Decimal("100.00")
        assert bal_a == Decimal("50.00")
        assert bal_b == Decimal("50.00")
