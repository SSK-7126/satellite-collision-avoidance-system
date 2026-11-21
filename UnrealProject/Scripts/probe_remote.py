import sys
import time

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

class Config(remote_execution.RemoteExecutionConfig):
    def __init__(self):
        super().__init__()
        self.multicast_bind_address = '0.0.0.0'

print("Probing Unreal Remote Execution...")
for attempt in range(10):
    remote = remote_execution.RemoteExecution(Config())
    remote.start()
    time.sleep(2.0)
    nodes = remote.remote_nodes
    remote.stop()
    if nodes:
        print(f"Connected on attempt {attempt+1}! Discovered node: {nodes[0]['node_id']} ({nodes[0]['engine_version']})")
        sys.exit(0)
    print(f"Attempt {attempt+1}: waiting for editor Python remote execution server...")

print("Timeout waiting for remote execution server.")
sys.exit(1)
