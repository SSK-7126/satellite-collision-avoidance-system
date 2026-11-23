"""
ue_runner.py
Helper to run python snippets or files in Unreal Editor via Remote Execution.
"""
import sys
import os
import time

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

def run_ue_code(code_string):
    remote = remote_execution.RemoteExecution()
    remote.start()
    
    start_time = time.time()
    while not remote.remote_nodes and (time.time() - start_time) < 4.0:
        time.sleep(0.3)
        
    if not remote.remote_nodes:
        print("[ERROR] No running Unreal remote nodes found after waiting.")
        remote.stop()
        sys.exit(1)
    
    node_id = remote.remote_nodes[0]["node_id"]
    remote.open_command_connection(node_id)
    result = remote.run_command(code_string)
    
    out_lines = []
    for entry in result.get("output", []):
        msg = entry.get("output", "")
        print(msg, end="")
        out_lines.append(msg)
        
    remote.stop()
    return "".join(out_lines)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-c" and len(sys.argv) > 2:
            run_ue_code(sys.argv[2])
        else:
            target_file = sys.argv[1]
            with open(target_file, "r", encoding="utf-8") as f:
                code = f.read()
            run_ue_code(code)
    else:
        print("Usage: python ue_runner.py <path_to_script.py> OR python ue_runner.py -c <code>")
