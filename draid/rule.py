'''
This module contains the definitions of the rule classes, and a few helper functions.
The rule classes contain their serialiser functions, usually called `dump`. See `parser` module for the deserialisers.
'''

from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from random import randint

from .proto import (
        ActivationCondition,
        Never,
        eq,
        dump,
        is_ac,
        obtain,
        Stage,
        AttributeValue,
        Attribute,
        )
from .exception import IllegalCaseError


PortedRules = Dict[str, Optional['DataRuleContainer']]


DanglingAttributeReference = Tuple[str, int]
DanglingObligatedAction = Tuple[str, List[DanglingAttributeReference]]
DanglingObligation = Tuple[DanglingObligatedAction, List[DanglingAttributeReference], Optional[ActivationCondition]]


def escaped(value: Any) -> Optional[str]:
    if isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return json.dumps(value)
    elif value is None:  # `None` may represent different meanings for different elements, so it should be treated separately where it is used
        return None
    else:
        return NotImplemented


class AttributeCapsule:

    # pylint: disable=protected-access
    @staticmethod
    def merge(first: 'AttributeCapsule', second: 'AttributeCapsule') -> Tuple['AttributeCapsule', List[int]]:
        assert first._name == second._name
        new = first.clone()
        diff = []
        for i, pr in enumerate(second._attrs):
            try:
                index = new._attrs.index(pr)
            except ValueError:
                index = len(new._attrs)
                new._attrs.append(pr)
            diff.append(index - i)
        return new, diff

    @staticmethod
    def from_raw(name: str, raw_attribute: List[Tuple[str, Any]]):
        attrs = []
        attrs.extend([Attribute(name, a_type, a_value) for (a_type, a_value) in raw_attribute])
        return AttributeCapsule(name, attrs)

    def __init__(self, name: str, attribute: List[Attribute]):
        self._name = name
        self._attrs = []  # type: List[Attribute]
        self._attrs.extend(attribute)
        for n in attribute:
            assert n.name == name

    def __repr__(self):
        return "{}[{}]".format(self._name, ",".join(map(repr, self._attrs)))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if not self._name == other._name:
                return False
            if not self._attrs == other._attrs:
                return False
            return True
        else:
            return NotImplemented

    def name(self) -> str:
        return self._name

    def dump(self) -> str:
        attr_strs = [f"{attr.type} {escaped(attr.value)}" for attr in self._attrs]
        return "attribute({}, [{}]).".format(self._name, ", ".join(attr_strs))

    def clone(self) -> 'AttributeCapsule':
        return AttributeCapsule(self._name, [a.clone() for a in self._attrs])

    def get(self, index: int) -> Attribute:
        return self._attrs[index]


class AttributeResolver:

    def __init__(self, attribute_capsule_map: Dict[str, AttributeCapsule]):
        self._amap = attribute_capsule_map

    def resolve(self, attribute_reference: Tuple[str, int]) -> Attribute:
        name, index = attribute_reference
        return self._amap[name].get(index)


class ActivatedObligation:

    def __init__(self, name: str, attributes: List[Attribute] = []):
        self.name = name
        self.attributes = attributes

    def __repr__(self):
        return f'({self.name} {self.attributes})'


class ObligationDeclaration:
    '''
    Obligation declaration is not stateful itself, but activated data rules are.
    There is no grouping of data rules, so it makes no sense to "merge" two data rules: two data rules that are exactly the same should have one removed. However, it makes sense to merge two activated data rules.
    '''

    @classmethod
    def from_raw(cls, obligated_action: DanglingObligatedAction, validity_binding: List[DanglingAttributeReference]=[], activation_condition_repr: Optional[str]=None):
        activation_condition = obtain(activation_condition_repr) if activation_condition_repr else None
        return cls(obligated_action, validity_binding, activation_condition)

    def __init__(self, obligated_action: Union[str, Tuple[str, List[Tuple[str, int]]]], validity_binding: List[Tuple[str, int]] = [], activation_condition: Optional[ActivationCondition] = None):
        if isinstance(obligated_action, str):
            self._name, self._attr_ref = obligated_action, []  # type: str, List[Tuple[str, int]]
        else:
            self._name, self._attr_ref = obligated_action
        self._validity_binding = validity_binding
        if not activation_condition:
            activation_condition = Never()
        self._ac = activation_condition

    def __repr__(self):
        return f"obligation ( ({self._name, self._attr_ref}), {self._attr_ref}, {self._ac} )"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._name != other._name:
                return False
            if self._attr_ref != other._attr_ref:
                return False
            if self._validity_binding != other._validity_binding:
                return False
            if not eq(self._ac, other._ac):
                return False
            return True
        else:
            return NotImplemented

    def dump(self) -> str:
        def dump_attr_ref(attr_refs):
            return (f"{attr_name}[{attr_index}]" for attr_name, attr_index in attr_refs)
        s_attr_ref = " ".join(dump_attr_ref(self._attr_ref))
        s_validity_binding = ','.join(dump_attr_ref(self._validity_binding))
        ac_dump = dump(self._ac)
        s_ac = f'"{ac_dump}"' if ac_dump else 'null'
        s = f"obligation({escaped(self._name)} {s_attr_ref}, [{s_validity_binding}], {s_ac})."
        return s

    def clone(self) -> 'ObligationDeclaration':
        return self._transfer({})

    def _transfer(self, dmap) -> 'ObligationDeclaration':
        def map_attr_refs(attr_refs):
            new_attr_refs = []
            for name, index in attr_refs:
                if dmap and name in dmap:
                    index = dmap[name][index]
                new_attr_refs.append((name, index))
            return new_attr_refs
        return ObligationDeclaration((self._name, map_attr_refs(self._attr_ref)), map_attr_refs(self._validity_binding), self._ac)

    def name(self):
        return self._name

    def on_stage(self, current_stage: Stage, function: Optional[str], attribute_resolver: AttributeResolver) -> Optional[ActivatedObligation]:
        if self._ac.is_met(current_stage, function):
            return ActivatedObligation(self._name, [attribute_resolver.resolve(attr_ref) for attr_ref in self._attr_ref])
        return None


class DataRuleContainer(AttributeResolver):

    # pylint: disable=protected-access
    @classmethod
    def merge(cls, first: 'DataRuleContainer', *rest: 'DataRuleContainer') -> 'DataRuleContainer':
        obligation_declarations = []
        attributes: Dict[str, List[Attribute]] = {}

        for drc in [first, *rest]:
            dmap: Dict[str, Dict[int, int]] = {}
            for attr_cap in drc._attrcaps:
                name = attr_cap.name()
                if name not in attributes: attributes[name] = []
                if name not in dmap: dmap[name] = {}
                for index, original_attr in enumerate(attr_cap._attrs):
                    if original_attr in attributes[name]:
                        dmap[name][index] = attributes[name].index(original_attr)
                    else:
                        dmap[name][index] = len(attributes[name])
                        attributes[name].append(original_attr)

            for ob_decl in drc._rules:
                ob_decl_new = ob_decl._transfer(dmap)
                if ob_decl_new not in obligation_declarations:
                    obligation_declarations.append(ob_decl_new)

        attribute_capsules = [AttributeCapsule(name, attrs) for name, attrs in attributes.items()]

        return DataRuleContainer(obligation_declarations, attribute_capsules)


    def __init__(self, rules: List[ObligationDeclaration], attribute_capsules: List[AttributeCapsule]):
        self._rules: List[ObligationDeclaration] = rules
        self._attrcaps: List[AttributeCapsule] = attribute_capsules
        super().__init__({atc.name(): atc for atc in attribute_capsules})

    def __repr__(self):
        return "DataRuleContainer(obligations: [{}] ; attributes: [{}])".format(
                ",".join(map(repr, self._rules)),
                ",".join(map(repr, self._attrcaps)),
                )

    def __eq__(self, other):
        # TODO: order independent
        if isinstance(other, self.__class__):
            if not self._rules == other._rules:
                return False
            if not self._attrcaps == other._attrcaps:
                return False
            if not self._amap == other._amap:
                return False
            return True
        else:
            return NotImplemented

    def dump(self) -> str:
        skeleton = """begin
        {}
        end
        """
        s_ob = "\n".join([r.dump() for r in self._rules])
        s_pr = "\n".join([pr.dump() for pr in self._amap.values()])
        s = s_ob
        if s_pr:
            s += '\n' + s_pr
        return skeleton.format(s)

    def clone(self) -> 'DataRuleContainer':
        rules = [r.clone() for r in self._rules]
        attrcaps = [atc.clone() for atc in self._attrcaps]
        return DataRuleContainer(rules, attrcaps)

    def on_stage(self, current_stage: Stage, function: Optional[str]) -> List[ActivatedObligation]:
        lst = []
        for r in self._rules:
            ret = r.on_stage(current_stage, function, self)
            if ret:
                lst.append(ret)
        return lst

    def summary(self) -> str:
        return "{} obligations, {} attributes".format(
                len(self._rules),
                len(self._attrcaps),
                )


def RandomRule(must=False) -> str:
    return random_rule(str(randint(0, 20)), must)


def random_rule(suffix='', must=False) -> str:
    if must:
        rint = randint(1, 2)
    else:
        rint = randint(0, 2)
    if not rint:
        return ""
    else:
        #activate_on_import = (False, True)[randint(0, 1)]
        activate_on_import = True
        if rint == 1:
            return rule_acknowledge('MySource', suffix, activate_on_import)
        else:
            return rule_account(suffix)


def rule_acknowledge(source: str, suffix='', activate_on_import=False) -> str:
    when = 'WhenImported ' if activate_on_import else ''
    return f'''
    begin
        obligation(Acknowledge, [source_name], {when}).
        attribute(source_name, ["str" "{source}{suffix}"]).
    end
    '''


def rule_account(suffix='') -> str:
    return f'''
    begin
        obligation(Account{suffix}, [], null).
    end
    '''


class FlowRule:
    '''
    FlowRule is stateless
    '''

    @staticmethod
    def map_name(name_map, name):
        return name_map[name] if name in name_map else name

    @dataclass
    class Propagate:
        input_port: str
        output_ports: List[str]

        def mapped(self, name_map):
            input_port = FlowRule.map_name(name_map, self.input_port)
            output_ports = [FlowRule.map_name(name_map, port) for port in self.output_ports]
            return FlowRule.Propagate(input_port, output_ports)

    @dataclass
    class Edit:
        new_type: str
        new_value: str
        input_port: Optional[str] = None
        output_port: Optional[str] = None
        name: Optional[str] = None
        match_type: Optional[str] = None
        match_value: Optional[Union[str, int, float]] = None

        def mapped(self, name_map):
            input_port = FlowRule.map_name(name_map, self.input_port)
            output_port = FlowRule.map_name(name_map, self.output_port)
            return FlowRule.Edit(self.new_type, self.new_value, input_port, output_port, self.name, self.match_type, self.match_value)

    @dataclass
    class Delete:
        input_port: Optional[str] = None
        output_port: Optional[str] = None
        name: Optional[str] = None
        match_type: Optional[str] = None
        match_value: Optional[Union[str, int, float]] = None

        def mapped(self, name_map):
            input_port = FlowRule.map_name(name_map, self.input_port)
            output_port = FlowRule.map_name(name_map, self.output_port)
            return FlowRule.Delete(input_port, output_port, self.name, self.match_type, self.match_value)

    Action = Union[Propagate, Edit, Delete]

    def __init__(self, actions: List[Action]):
        self.actions = actions
        self.name_map = None  # type: Optional[Dict[str, str]]

    def set_name_map(self, name_map: Dict[str, str]):
        self.name_map = name_map

    def mapped_actions(self) -> List[Action]:
        '''
        Returns the actions with name mapped.
        '''
        if not self.name_map:
            return self.actions
        else:
            return [action.mapped(self.name_map) for action in self.actions]

    def dump(self) -> str:
        def optional(s):
            return s or '*'
        s = ''
        for action in self.actions:
            if isinstance(action, FlowRule.Propagate):
                s += f"{action.input_port} -> {', '.join(action.output_ports)}\n"
            elif isinstance(action, FlowRule.Edit):
                s += f"edit({optional(escaped(action.input_port))}, {optional(escaped(action.output_port))}, {optional(action.name)}, {optional(escaped(action.match_type))}, {optional(escaped(action.match_value))}, {escaped(action.new_type)}, {escaped(action.new_value)})\n"
            elif isinstance(action, FlowRule.Delete):
                s += f"delete({optional(escaped(action.input_port))}, {optional(escaped(action.output_port))}, {optional(action.name)}, {optional(escaped(action.match_type))}, {optional(escaped(action.match_value))})\n"
            else:
                raise IllegalCaseError()
        return s

    def __iter__(self):
        return self.mapped_actions().__iter__()

    def __eq__(self, other):
        # TODO: order independent
        if isinstance(other, self.__class__):
            if not self.actions == other.actions:
                return False
            if not self.name_map == other.name_map:
                return False
            return True
        else:
            return NotImplemented


Propagate = FlowRule.Propagate
Edit = FlowRule.Edit
Delete = FlowRule.Delete


def DefaultFlow(input_ports: List[str], output_ports: List[str]) -> FlowRule:
    actions = []  # type: List[FlowRule.Action]
    for input_port in input_ports:
        pr = FlowRule.Propagate(input_port, output_ports)
        actions.append(pr)
    return FlowRule(actions)
