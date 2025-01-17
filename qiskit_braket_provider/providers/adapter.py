"""Util function for provider."""
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

from braket.aws import AwsDevice
from braket.circuits import (
    Circuit,
    FreeParameter,
    Instruction,
    Gate,
    Qubit,
    QubitSet,
    gates,
    result_types,
    observables,
)
from braket.device_schema import (
    DeviceActionType,
    GateModelQpuParadigmProperties,
    JaqcdDeviceActionProperties,
    OpenQASMDeviceActionProperties,
)
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.oqc import OqcDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.device_schema.simulators import (
    GateModelSimulatorDeviceCapabilities,
    GateModelSimulatorParadigmProperties,
)
from braket.devices import LocalSimulator
from numpy import pi
from qiskit import QuantumCircuit
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit import Measure, Parameter
from qiskit.circuit.library import (
    CCXGate,
    CPhaseGate,
    CSwapGate,
    CXGate,
    CYGate,
    CZGate,
    ECRGate,
    HGate,
    IGate,
    iSwapGate,
    PhaseGate,
    RXGate,
    RXXGate,
    RYGate,
    RYYGate,
    RZGate,
    RZZGate,
    SdgGate,
    SGate,
    SwapGate,
    SXdgGate,
    SXGate,
    TdgGate,
    TGate,
    UGate,
    U1Gate,
    U2Gate,
    U3Gate,
    XGate,
    XXPlusYYGate,
    YGate,
    ZGate,
)
from qiskit.transpiler import InstructionProperties, Target

from qiskit_braket_provider.exception import QiskitBraketException

qiskit_to_braket_gate_names_mapping = {
    "u": "u",
    "u1": "u1",
    "u2": "u2",
    "u3": "u3",
    "p": "phaseshift",
    "cx": "cnot",
    "x": "x",
    "y": "y",
    "z": "z",
    "t": "t",
    "tdg": "ti",
    "s": "s",
    "sdg": "si",
    "sx": "v",
    "sxdg": "vi",
    "swap": "swap",
    "rx": "rx",
    "ry": "ry",
    "rz": "rz",
    "rzz": "zz",
    "id": "i",
    "h": "h",
    "cy": "cy",
    "cz": "cz",
    "ccx": "ccnot",
    "cswap": "cswap",
    "cp": "cphaseshift",
    "rxx": "xx",
    "ryy": "yy",
    "ecr": "ecr",
}


qiskit_gate_names_to_braket_gates: Dict[str, Callable] = {
    "u": lambda theta, phi, lam: [
        gates.Rz(lam),
        gates.Rx(pi / 2),
        gates.Rz(theta),
        gates.Rx(-pi / 2),
        gates.Rz(phi),
    ],
    "u1": lambda lam: [gates.Rz(lam)],
    "u2": lambda phi, lam: [gates.Rz(lam), gates.Ry(pi / 2), gates.Rz(phi)],
    "u3": lambda theta, phi, lam: [
        gates.Rz(lam),
        gates.Rx(pi / 2),
        gates.Rz(theta),
        gates.Rx(-pi / 2),
        gates.Rz(phi),
    ],
    "p": lambda angle: [gates.PhaseShift(angle)],
    "cp": lambda angle: [gates.CPhaseShift(angle)],
    "cx": lambda: [gates.CNot()],
    "x": lambda: [gates.X()],
    "y": lambda: [gates.Y()],
    "z": lambda: [gates.Z()],
    "t": lambda: [gates.T()],
    "tdg": lambda: [gates.Ti()],
    "s": lambda: [gates.S()],
    "sdg": lambda: [gates.Si()],
    "sx": lambda: [gates.V()],
    "sxdg": lambda: [gates.Vi()],
    "swap": lambda: [gates.Swap()],
    "rx": lambda angle: [gates.Rx(angle)],
    "ry": lambda angle: [gates.Ry(angle)],
    "rz": lambda angle: [gates.Rz(angle)],
    "rzz": lambda angle: [gates.ZZ(angle)],
    "id": lambda: [gates.I()],
    "h": lambda: [gates.H()],
    "cy": lambda: [gates.CY()],
    "cz": lambda: [gates.CZ()],
    "ccx": lambda: [gates.CCNot()],
    "cswap": lambda: [gates.CSwap()],
    "rxx": lambda angle: [gates.XX(angle)],
    "ryy": lambda angle: [gates.YY(angle)],
    "ecr": lambda: [gates.ECR()],
}

qiskit_gate_name_to_braket_gate_mapping: Dict[str, Optional[QiskitInstruction]] = {
    "u": UGate(Parameter("theta"), Parameter("phi"), Parameter("lam")),
    "u1": U1Gate(Parameter("theta")),
    "u2": U2Gate(Parameter("theta"), Parameter("lam")),
    "u3": U3Gate(Parameter("theta"), Parameter("phi"), Parameter("lam")),
    "h": HGate(),
    "ccnot": CCXGate(),
    "cnot": CXGate(),
    "cphaseshift": CPhaseGate(Parameter("theta")),
    #"cphaseshift00": CPhaseGate(Parameter("theta")), ## EDIT
    #"cphaseshift01": CPhaseGate(Parameter("theta")), ## EDIT
    #"cphaseshift10": CPhaseGate(Parameter("theta")), ## EDIT
    "cswap": CSwapGate(),
    "cy": CYGate(),
    "cz": CZGate(),
    "i": IGate(),
    "iswap": iSwapGate(),
    "phaseshift": PhaseGate(Parameter("theta")),
    #"pswap": #[[1,0,0,0],[0,0,exp(1j*phi),0],[0,exp(1j*phi),0,0],[0,0,0,1]]
    "rx": RXGate(Parameter("theta")),
    "ry": RYGate(Parameter("theta")),
    "rz": RZGate(Parameter("phi")),
    "s": SGate(),
    "si": SdgGate(),
    "swap": SwapGate(),
    "t": TGate(),
    "ti": TdgGate(),
    "v": SXGate(),
    "vi": SXdgGate(),
    "x": XGate(),
    "xx": RXXGate(Parameter("theta")),
    "xy": XXPlusYYGate(Parameter("theta")),
    "y": YGate(),
    "yy": RYYGate(Parameter("theta")),
    "z": ZGate(),
    "zz": RZZGate(Parameter("theta")),
    "ecr": ECRGate(),
}


def _op_to_instruction(operation: str) -> Optional[QiskitInstruction]:
    """Converts Braket operation to Qiskit Instruction.

    Args:
        operation: operation

    Returns:
        Circuit Instruction
    """
    operation = operation.lower()
    return qiskit_gate_name_to_braket_gate_mapping.get(operation, None)


def local_simulator_to_target(simulator: LocalSimulator) -> Target:
    """Converts properties of LocalSimulator into Qiskit Target object.

    Args:
        simulator: AWS LocalSimulator

    Returns:
        target for Qiskit backend
    """
    target = Target()

    instructions = [
        inst
        for inst in qiskit_gate_name_to_braket_gate_mapping.values()
        if inst is not None
    ]
    properties = simulator.properties
    paradigm: GateModelSimulatorParadigmProperties = properties.paradigm

    # add measurement instruction
    target.add_instruction(Measure(), {(i,): None for i in range(paradigm.qubitCount)})

    for instruction in instructions:
        instruction_props: Optional[
            Dict[Union[Tuple[int], Tuple[int, int]], Optional[InstructionProperties]]
        ] = {}

        if instruction.num_qubits == 1:
            for i in range(paradigm.qubitCount):
                instruction_props[(i,)] = None
            target.add_instruction(instruction, instruction_props)
        elif instruction.num_qubits == 2:
            for src in range(paradigm.qubitCount):
                for dst in range(paradigm.qubitCount):
                    if src != dst:
                        instruction_props[(src, dst)] = None
                        instruction_props[(dst, src)] = None
            target.add_instruction(instruction, instruction_props)

    return target


def aws_device_to_target(device: AwsDevice) -> Target:
    """Converts properties of Braket device into Qiskit Target object.

    Args:
        device: AWS Braket device

    Returns:
        target for Qiskit backend
    """
    # building target
    target = Target(description=f"Target for AWS Device: {device.name}")

    properties = device.properties
    # gate model devices
    if isinstance(
        properties,
        (IonqDeviceCapabilities, RigettiDeviceCapabilities, OqcDeviceCapabilities),
    ):
        action_properties: OpenQASMDeviceActionProperties = (
            properties.action.get(DeviceActionType.OPENQASM)
            if properties.action.get(DeviceActionType.OPENQASM)
            else properties.action.get(DeviceActionType.JAQCD)
        )
        paradigm: GateModelQpuParadigmProperties = properties.paradigm
        connectivity = paradigm.connectivity
        instructions: List[QiskitInstruction] = []

        for operation in action_properties.supportedOperations:
            instruction = _op_to_instruction(operation)
            if instruction is not None:
                # TODO: remove when target will be supporting > 2 qubit gates  # pylint:disable=fixme
                if instruction.num_qubits <= 2:
                    instructions.append(instruction)

        # add measurement instructions
        target.add_instruction(
            Measure(), {(i,): None for i in range(paradigm.qubitCount)}
        )

        for instruction in instructions:
            instruction_props: Optional[
                Dict[
                    Union[Tuple[int], Tuple[int, int]], Optional[InstructionProperties]
                ]
            ] = {}
            # adding 1 qubit instructions
            if instruction.num_qubits == 1:
                for i in range(paradigm.qubitCount):
                    instruction_props[(i,)] = None
            # adding 2 qubit instructions
            elif instruction.num_qubits == 2:
                # building coupling map for fully connected device
                if connectivity.fullyConnected:
                    for src in range(paradigm.qubitCount):
                        for dst in range(paradigm.qubitCount):
                            if src != dst:
                                instruction_props[(src, dst)] = None
                                instruction_props[(dst, src)] = None
                # building coupling map for device with connectivity graph
                else:
                    for src, connections in connectivity.connectivityGraph.items():
                        for dst in connections:
                            instruction_props[(int(src), int(dst))] = None
            # for more than 2 qubits
            else:
                instruction_props = None

            target.add_instruction(instruction, instruction_props)

    # gate model simulators
    elif isinstance(properties, GateModelSimulatorDeviceCapabilities):
        simulator_action_properties: JaqcdDeviceActionProperties = (
            properties.action.get(DeviceActionType.JAQCD)
        )
        simulator_paradigm: GateModelSimulatorParadigmProperties = properties.paradigm
        instructions = []

        for operation in simulator_action_properties.supportedOperations:
            instruction = _op_to_instruction(operation)
            if instruction is not None:
                # TODO: remove when target will be supporting > 2 qubit gates  # pylint:disable=fixme
                if instruction.num_qubits <= 2:
                    instructions.append(instruction)

        # add measurement instructions
        target.add_instruction(
            Measure(), {(i,): None for i in range(simulator_paradigm.qubitCount)}
        )

        for instruction in instructions:
            simulator_instruction_props: Optional[
                Dict[
                    Union[Tuple[int], Tuple[int, int]],
                    Optional[InstructionProperties],
                ]
            ] = {}
            # adding 1 qubit instructions
            if instruction.num_qubits == 1:
                for i in range(simulator_paradigm.qubitCount):
                    simulator_instruction_props[(i,)] = None
            # adding 2 qubit instructions
            elif instruction.num_qubits == 2:
                # building coupling map for fully connected device
                for src in range(simulator_paradigm.qubitCount):
                    for dst in range(simulator_paradigm.qubitCount):
                        if src != dst:
                            simulator_instruction_props[(src, dst)] = None
                            simulator_instruction_props[(dst, src)] = None
            target.add_instruction(instruction, simulator_instruction_props)

    else:
        raise QiskitBraketException(
            f"Cannot convert to target. "
            f"{properties.__class__} device capabilities are not supported yet."
        )

    return target


def convert_qiskit_to_braket_circuit(circuit: QuantumCircuit) -> Circuit:
    """Return a Braket quantum circuit from a Qiskit quantum circuit.
     Args:
            circuit (QuantumCircuit): Qiskit Quantum Cricuit

    Returns:
        Circuit: Braket circuit
    """
    quantum_circuit = Circuit()
    for qiskit_gates in circuit.data:
        name = qiskit_gates[0].name
        if name == "measure":
            # TODO: change Probability result type for Sample for proper functioning # pylint:disable=fixme
            # Getting the index from the bit mapping
            quantum_circuit.add_result_type(
                # pylint:disable=fixme
                result_types.Sample(
                    observable=observables.Z(),
                    target=[
                        circuit.find_bit(qiskit_gates[1][0]).index,
                        circuit.find_bit(qiskit_gates[2][0]).index,
                    ],
                )
            )
        elif name == "barrier":
            # This does not exist
            pass
        else:
            params = []
            if hasattr(qiskit_gates[0], "params"):
                params = qiskit_gates[0].params

            for i, param in enumerate(params):
                if isinstance(param, Parameter):
                    params[i] = FreeParameter(param.name)

            for gate in qiskit_gate_names_to_braket_gates[name](*params):
                instruction = Instruction(
                    # Getting the index from the bit mapping
                    operator=gate,
                    target=[circuit.find_bit(i).index for i in qiskit_gates[1]],
                )
                quantum_circuit += instruction
    return quantum_circuit


def convert_qiskit_to_braket_circuits(
    circuits: List[QuantumCircuit],
) -> Iterable[Circuit]:
    """Converts all Qiskit circuits to Braket circuits.
     Args:
            circuits (List(QuantumCircuit)): Qiskit Quantum Cricuit

    Returns:
        Circuit (Iterable[Circuit]): Braket circuit
    """
    for circuit in circuits:
        yield convert_qiskit_to_braket_circuit(circuit)


def set_qubits(size, target, control) -> Union[tuple, int]:
    from qiskit.circuit import Qubit
    qubits = []
    for c in control:
        qubits.append(Qubit(QuantumRegister(size, 'q'), c.real))
    for t in target:
        qubits.append(Qubit(QuantumRegister(size, 'q'), t.real))
                
    return tuple(qubits), len(tuple(qubits))

def set_control(num_controls: int, gate: str):
    if num_controls <= 0:
        name = gate
    elif num_controls == 1:
        name = "c" + gate
    elif num_controls == 2:
        name = "cc" + gate
    elif num_controls > 2:
        if gate == "cx":
            name = "m" + gate
        else:
            name = "c" + str(num_controls) + gate
    return name

def from_braket_circuit(circuit: Circuit) -> QuantumCircuit:
    """Return a Qiskit quantum circuit from a Braket quantum circuit.
     
    Args:
        circuit (Circuit): Braket Quantum Circuit

    Returns:
        QuantumCircuit: Qiskit Quantum circuit
    """
    
    num_qubits = circuit.qubit_count - 1

    for circ_instruction in circuit.instructions:
        for c in circ_instruction.control:
            if c.real > num_qubits:
                num_qubits = c.real 
        for t in circ_instruction.target:
            if t.real > num_qubits:
                num_qubits = t.real
    
    num_qubits += 1
    quantum_circuit = QuantumCircuit(num_qubits)#, num_qubits)
        
    from qiskit.circuit import CircuitInstruction, Instruction
        
    for circ_instruction in circuit.instructions:
        
        operator = circ_instruction.operator
        
        instruction = _op_to_instruction(operator.name)
        
        if instruction == None:
            raise Exception(f"Braket gate \"{operator.name}\" not supported in Qiskit") 
        
        instruction.name = operator.name.lower()
        _, instruction.num_qubits = set_qubits(num_qubits, circ_instruction.target, circ_instruction.control)
        params = instruction.params = []
        
        #if hasattr(circ_instruction, "power"):
        #    print("power:", circ_instruction.power)
            
        if hasattr(circ_instruction, "control"):
            instruction.name = set_control(len(circ_instruction.control), operator.name.lower())            

        if hasattr(operator, "angle"):
            if isinstance(operator.angle, FreeParameter):
                print(operator)
                import copy as cp
                p = Parameter(operator.angle.name)
                print(p)
                instruction.params = [p]
            else:
                instruction.params = [operator.angle]
                
        qubits = []
        for qubit in circ_instruction.control:
            qubits.append(qubit)
        for qubit in circ_instruction.target:
            qubits.append(qubit)

        quantum_circuit.append(instruction.copy(), QubitSet(qubits))
                
    if circuit.result_types == []:
        quantum_circuit.measure_all()
    else:   
        for qubits in result_type.target:
            quantum_circuit.measure(qubits.real, qubits.real)        
        
    return quantum_circuit

def from_braket_circuits(
    circuits: List[Circuit],
) -> Iterable[QuantumCircuit]:
    """Converts all Braket circuits to Qiskit circuits.
     
    Args:
        circuits (List(Circuit)): Braket circuit

    Returns:
        QuantumCircuit (Iterable[QuantumCircuit]): Qiskit Quantum Circuit
    """
    for circuit in circuits:
        yield from_braket_circuit(circuit)


def wrap_circuits_in_verbatim_box(circuits: List[Circuit]) -> Iterable[Circuit]:
    """Convert each Braket circuit an equivalent one wrapped in verbatim box.

    Args:
           circuits (List(Circuit): circuits to be wrapped in verbatim box.
    Returns:
           Circuits wrapped in verbatim box, comprising the same instructions
           as the original one and with result types preserved.
    """
    return [
        Circuit(circuit.result_types).add_verbatim_box(Circuit(circuit.instructions))
        for circuit in circuits
    ]
