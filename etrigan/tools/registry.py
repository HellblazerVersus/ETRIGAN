from typing import Dict, Any, Callable
from etrigan.tools.fs import fs_list, fs_read, fs_write
from etrigan.tools.sandbox import execute_sandboxed_code
from etrigan.deliver.generators import generate_approval_note, generate_calculation_sheet

TOOL_REGISTRY: Dict[str, Callable] = {
    "fs.list": lambda args: fs_list(args.get("subpath", "")),
    "fs.read": lambda args: fs_read(args.get("path", ""), args.get("max_chars", 15000)),
    "fs.write": lambda args: fs_write(args.get("path", ""), args.get("content", "")),
    "code.run": lambda args: execute_sandboxed_code(args.get("code", ""), args.get("timeout", 45)),
    "deliver.docx": lambda args: {
        "status": "success",
        "file": generate_approval_note(
            subject=args.get("subject", "Engineering Note"),
            findings=args.get("findings", ["Observations verified"]),
            recommendation=args.get("recommendation", "Approve as requested")
        )
    },
    "deliver.xlsx": lambda args: {
        "status": "success",
        "file": generate_calculation_sheet(
            equipment_tag=args.get("equipment_tag", "EQUIP-01"),
            readings=args.get("readings", []),
            min_thickness=args.get("min_thickness", 3.5)
        )
    }
}

def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name not in TOOL_REGISTRY:
        return {"success": False, "error": f"Tool '{tool_name}' not found in registry."}
    try:
        handler = TOOL_REGISTRY[tool_name]
        res = handler(args)
        if isinstance(res, dict) and "success" in res:
            return res
        return {"success": True, "output": res}
    except Exception as e:
        return {"success": False, "error": str(e)}
