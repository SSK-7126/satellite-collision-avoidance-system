with open('UnrealProject/Intermediate/PythonStub/unreal.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class SimulationDataBridge')
if idx != -1:
    end_doc = text.find('"""', idx + 50)
    print(text[end_doc:end_doc+2000])
