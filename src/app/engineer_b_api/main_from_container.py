from fastapi import Body

@app.post("/api/patches/{patch_id}/apply")
async def apply_manual_patch_inline(patch_id: str, approve_token: str = Body(None)):
    return {
        "patch_id": patch_id,
        "status": "received-inline",
        "approve_token": approve_token,
    }
