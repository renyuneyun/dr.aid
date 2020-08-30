
import logging
from typing import Dict, List, Optional, Tuple, Union
from random import randint

from .proto import (
        ActivationCondition,
        Never,
        eq,
        dump,
        Stage,
        AttributeValue,
        Attribute,
        )


PortedRules = Dict[str, Optional['DataRuleContainer']]


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

    def __init__(self, name: str, raw_attribute: Optional[Union[str, List[str]]] = None, attribute: Optional[List[Attribute]] = None):
        self._name = name
        self._attrs = []  # type: List[Attribute]
        if raw_attribute:
            if isinstance(raw_attribute, str):
                self._attrs.append(Attribute.instantiate(name, raw_attribute))
            else:
                self._attrs.extend([Attribute.instantiate(name, at) for at in raw_attribute])
        elif attribute:
            self._attrs.extend(attribute)
        else:
            raise RuntimeError("Trying to instantiate AttributeCapsule without attribute")

    def __repr__(self):
        return "{}[{}]".format(self._name, ",".join(map(lambda a: a.__repr__(), self._attrs)))

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
        attr_objs = [at.get().value() for at in self._attrs]
        attr_strs = [str(at) for at in attr_objs]
        return "attribute {} [{}].".format(self._name, ", ".join(attr_strs))

    def clone(self) -> 'AttributeCapsule':
        return AttributeCapsule(self._name, attribute=[a.clone() for a in self._attrs])

    def get(self, index: int) -> Attribute:
        return self._attrs[index]

class AttributeResolver:

    def __init__(self, attribute_capsule_map: Dict[str, AttributeCapsule]):
        self._amap = attribute_capsule_map

    def resolve(self, attribute_reference: Tuple[str, int]) -> Attribute:
        name, index = attribute_reference
        return self._amap[name].get(index)


class ActivatedObligation:

    def __init__(self, name: str, attribute: Optional[Attribute] = None):
        self._name = name
        self._attribute = attribute

    def __repr__(self):
        return f'({self._name} {self._attribute})'


class ObligationDeclaration:
    '''
    Obligation declaration is not stateful itself, but activated data rules are.
    There is no grouping of data rules, so it makes no sense to "merge" two data rules: two data rules that are exactly the same should have one removed. However, it makes sense to merge two activated data rules.
    '''

    def __init__(self, name: str, attribute: Optional[Tuple[str, int]] = None, activation_condition: Optional[ActivationCondition] = None):
        self._name = name
        self._attribute = attribute
        if not activation_condition:
            activation_condition = Never()
        self._ac = activation_condition

    def __repr__(self):
        return "obligation ({} {}) ({})".format(self._name, self._attribute, self._ac)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._name != other._name:
                return False
            if self._attribute != other._attribute:
                return False
            if not eq(self._ac, other._ac):
                return False
            return True
        else:
            return NotImplemented

    def dump(self) -> str:
        s = "obligation {}".format(self._name)
        if self._attribute:
            s = "{} {}[{}]".format(s, self._attribute[0], self._attribute[1])
        ac_dump = dump(self._ac)
        if ac_dump:
            s += ' {}'.format(ac_dump)
        s += " ."
        return s

    def clone(self) -> 'ObligationDeclaration':
        return self._transfer({})

    def _transfer(self, dmap) -> 'ObligationDeclaration':
        if self._attribute:
            index = self._attribute[1]
            if dmap and self._attribute[0] in dmap:
                index += dmap[self._attribute[0]][index]
            new_attribute = (self._attribute[0], index)
            return ObligationDeclaration(self._name, new_attribute, self._ac)
        return ObligationDeclaration(self._name, activation_condition=self._ac)

    def name(self):
        return self._name

    def on_stage(self, current_stage: Stage, attribute_resolver: AttributeResolver) -> Optional[ActivatedObligation]:
        if self._ac.is_met(current_stage):
            if self._attribute:
                return ActivatedObligation(self._name, attribute_resolver.resolve(self._attribute))
            else:
                return ActivatedObligation(self._name)
        return None


class DataRuleContainer(AttributeResolver):

    # pylint: disable=protected-access
    @classmethod
    def merge(cls, first: 'DataRuleContainer', *rest: 'DataRuleContainer') -> 'DataRuleContainer':
        new = first.clone()
        for nxt in rest:
            dmap = {}
            for pname, pr in nxt._amap.items():
                if pname in new._amap:
                    pr, diff = AttributeCapsule.merge(new._amap[pname], pr)
                else:
                    diff = None  # type: ignore
                new._amap[pname] = pr
                if diff is not None:
                    dmap[pname] = diff
            new._attrcaps = [v for v in new._amap.values()]
            for r in nxt._rules:
                r = r._transfer(dmap)
                if r in new._rules:
                    continue
                new._rules.append(r)
        return new

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
        skeleton = """rule {} begin
        {}
        end
        """
        name = ''
        s_ob = "\n".join([r.dump() for r in self._rules])
        s_pr = "\n".join([pr.dump() for pr in self._amap.values()])
        s = s_ob
        if s_pr:
            s += '\n' + s_pr
        return skeleton.format(name, s)

    def clone(self) -> 'DataRuleContainer':
        rules = [r.clone() for r in self._rules]
        attrcaps = [atc.clone() for atc in self._attrcaps]
        return DataRuleContainer(rules, attrcaps)

    def on_stage(self, current_stage: Stage) -> List[ActivatedObligation]:
        lst = []
        for r in self._rules:
            ret = r.on_stage(current_stage, self)
            if ret:
                lst.append(ret)
        return lst

    def summary(self) -> str:
        return "{} obligations, {} attributes)".format(
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
    rule Rule0
        obligation Acknowledge source_name {when}.
        attribute source_name {source}{suffix} .
    end
    '''


def rule_account(suffix='') -> str:
    return f'''
    rule Rule1
        obligation Account{suffix} .
    end
    '''


class Propagate:
    def __init__(self, input_port, output_port):
        self.input_port = input_port
        self.output_port = output_port


class Delete:
    def __init__(self, input_port, output_port, name, a_type, value):
        self.input_port = input_port
        self.output_port = output_port
        self.name = name
        self.type = a_type
        self.value = value


class FlowRule:
    '''
    FlowRule is stateless
    '''

    # TODO: def __init__(self, connectivity, input_ports, output_ports):
    def __init__(self, connectivity):
        self._conn = connectivity

    def dump(self) -> str:
        s = ''
        for oport in self._conn:
            for iport in self._conn[oport]:
                s += "{} -> {}\n".format(iport, oport)
        return s


def DefaultFlow(input_ports: List[str], output_ports: List[str]) -> FlowRule:
    connectivity = {}
    # for output_port in output_ports:
    #     connectivity[output_port] = [p for p in input_ports]
    for input_port in input_ports:
        connectivity[input_port] = [p for p in output_ports]
    return FlowRule(connectivity)
