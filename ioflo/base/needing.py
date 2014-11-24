"""needing.py need action module

"""
#print("module {0}".format(__name__))

import time
import struct
from collections import deque
import inspect


from .globaling import *
from .odicting import odict
from . import aiding
from . import excepting
from . import registering
from . import storing
from . import acting
from . import tasking
from . import framing

from .consoling import getConsole
console = getConsole()

class Need(acting.Actor):
    """Need Class for conditions  such as entry or trans
    """
    Registry = odict()

    def expose(self):
        """
        """
        print("Need %s " % (self.name))

    @staticmethod
    def Check(state, comparison, goal, tolerance):
        """Check state compared to goal with tolerance
           tolerance ignored unless comparison == or !=
        """
        if comparison == '==':
            try: #in case goal is string
                result = ( (goal - abs(tolerance)) <= state <= (goal + abs(tolerance)))
            except TypeError:
                result = (goal == state)
        elif comparison == '<':
            result = ( state < goal)
        elif comparison == '<=':
            result = ( state <= goal)
        elif comparison == '>=':
            result = ( state >= goal)
        elif comparison == '>':
            result = ( state > goal)
        elif comparison == '!=':
            try: #in case goal is string
                result = ( state <= (goal - abs(tolerance)) or state >= (goal + abs(tolerance)) )
            except TypeError:
                result = (goal != state)
        else:
            result = False

        return result

class NeedAlways(Need):
    """NeedAlways Need  Special Need"""
    def action(self, **kw):
        """Always return true"""
        result = True
        console.profuse("Need Always = {0}\n".format(result))
        return result

class NeedDone(Need):
    """NeedDone Need Special Need"""
    def action(self, tasker, **kw):
        """
        Check if  tasker done
        parameters:
            tasker
        """
        result = tasker.done
        console.profuse("Need Framer {0} done = {1}\n".format(tasker.name, result))

        return result

    def resolve(self, tasker, **kwa):
        """Resolves value (tasker) link that is passed in as tasker parm
           resolved link is passed back to container act to update in act's parms
        """
        parms = super(NeedDone, self).resolve( **kwa)
        parms['tasker'] = tasker = tasking.resolveTasker(tasker,
                                                         who=self.name,
                                                         desc='need done tasker',
                                                         contexts=[],
                                                         human=self.act.human,
                                                         count=self.act.count)
        return parms #return items are updated in original act parms

    def cloneParms(self, parms, clones, **kw):
        """ Returns parms fixed up for framing cloning. This includes:
            Reverting any Frame links to name strings,
            Reverting non cloned Framer links into name strings
            Replacing any cloned framer links with the cloned name strings from clones
            Replacing any parms that are acts with clones.

            clones is dict whose items keys are original framer names
            and values are duples of (original,clone) framer references
        """
        parms = super(NeedStatus,self).cloneParms(parms, clones, **kw)

        tasker = parms.get('tasker')

        if isinstance(tasker, tasking.Tasker):
            if tasker.name in clones:
                parms['tasker'] = clones[tasker.name][1].name
            else:
                parms['tasker'] = tasker.name # revert to name
        elif tasker: # assume namestring
            if tasker in clones:
                parms['tasker'] = clones[tasker][1].name

        return parms

class NeedStatus(Need):
    """NeedStatus Need Special Need """
    def action(self, tasker, status, **kw):
        """
        Check if  tasker done
        parameters:
          tasker
          status
        """

        result = (tasker.status == status)
        console.profuse("Need Tasker {0} status is {1} = {2}\n".format(
            tasker.name, StatusNames[status], result))

        return result

    def resolve(self, tasker, **kwa):
        """Resolves value (tasker) link that is passed in as parm
           resolved link is passed back to container act to update in act's parms
        """
        parms = super(NeedStatus, self).resolve( **kwa)
        parms['tasker'] = tasker = tasking.resolveTasker(tasker,
                                                         who=self.name,
                                                         desc='need status tasker',
                                                         contexts=[],
                                                         human=self.act.human,
                                                         count=self.act.count)
        return parms #return items are updated in original act parms

    def cloneParms(self, parms, clones, **kw):
        """ Returns parms fixed up for framing cloning. This includes:
            Reverting any Frame links to name strings,
            Reverting non cloned Framer links into name strings
            Replacing any cloned framer links with the cloned name strings from clones
            Replacing any parms that are acts with clones.

            clones is dict whose items keys are original framer names
            and values are duples of (original,clone) framer references
        """
        parms = super(NeedStatus,self).cloneParms(parms, clones, **kw)

        tasker = parms.get('tasker')

        if isinstance(tasker, tasking.Tasker):
            if tasker.name in clones:
                parms['tasker'] = clones[tasker.name][1].name
            else:
                parms['tasker'] = tasker.name # revert to name
        elif tasker: # assume namestring
            if tasker in clones:
                parms['tasker'] = clones[tasker][1].name

        return parms

class NeedBoolean(Need):
    """NeedBoolean Need Special Need

       if state
    """
    def resolve(self, state, stateField, **kwa):
        """
        Resolves state share

        parms:
            state       share path of state
            stateField  state share field name
        """
        parms = super(NeedBoolean, self).resolve( **kwa)

        #convert state path to share and create field if necessary
        parms['state'] = state = self.resolvePath(ipath=state,
                                                  warn=True) # now a share

        if not stateField: #default rules for field
            if state: #state has fields
                if 'value' in state:
                    stateField = 'value'

                else: #ambiguous
                    msg = ("ResolveError: Can't determine field for state"
                          " '{0}'".format(state.name))
                    raise excepting.ResolveError(msg, 'state', self.name,
                                            self.act.human, self.act.count)
            else:
                stateField = 'value'

        if stateField not in state:
            console.profuse("     Warning: Non-existent field '{0}' in state {1}"
                            " ... creating anyway".format(stateField, state.name))
            state[stateField] = 0.0 #create

        parms['stateField'] = stateField

        return parms #return items are updated in original act parms

    def action(self, state, stateField, **kw):
        """ Check if state[stateField] evaluates to True
            parameters:
              state = share of state
              stateField = field key

        """
        if state[stateField]:
            result = True
        else:
            result = False
        console.profuse("Need Boolean, if {0}[{1}]: = {2}\n".format(
            state.name, stateField, result))

        return result

class NeedDirect(Need):
    """NeedDirect Need

       if state comparison goal [+- tolerance]
    """
    def resolve(self, state, stateField, comparison, goal, tolerance, **kwa):
        """
        Resolves state share

        parms:
            state       share path of state
            stateField  state share field name
            comparison  comparison operator string
            goal        goal value
            tolerance   tolerance value

        """
        parms = super(NeedDirect, self).resolve( **kwa)

        #convert state path to share and create field if necessary
        parms['state'] = state = self.resolvePath(ipath=state,
                                                  warn=True) # now a share

        if not stateField: #default rules for field
            if state: #state has fields
                if 'value' in state:
                    stateField = 'value'

                else: #ambiguous
                    msg = ("ResolveError: Can't determine field for state"
                          " '{0}'".format(state.name))
                    raise excepting.ResolveError(msg, 'state', self.name,
                                                self.act.human, self.act.count)
            else:
                stateField = 'value'

        if stateField not in state:
            console.profuse("     Warning: Non-existent field '{0}' in state {1}"
                            " ... creating anyway".format(stateField, state.name))
            state[stateField] = 0.0 #create

        parms['stateField'] = stateField

        return parms #return items are updated in original act parms

    def action(self, state, stateField, comparison, goal, tolerance, **kw):
        """ Check if state[field] comparison to goal +- tolerance is True
            parameters:
                state = share of state
                stateField = field key
                comparison
                goal
                tolerance

        """
        result = self.Check(state[stateField], comparison, goal, tolerance)
        console.profuse("Need Direct, if {0}[{1}] {2} {3} +- {4}: = {5}\n".format(
            state.name, stateField, comparison, goal, tolerance, result))

        return result

class NeedIndirect(Need):
    """NeedIndirect Need

       if state comparison goal [+- tolerance]
    """
    def resolve(self, state, stateField, comparison, goal, goalField, tolerance, **kwa):
        """
        Resolves state share

        parms:
            state       share path of state
            stateField  state share field name
            comparison  comparison operator string
            goal        share path of goal
            goalField   goal share field name
            tolerance   tolerance value

        """
        parms = super(NeedIndirect, self).resolve( **kwa)

        #convert state path to share and create field if necessary
        parms['state'] = state = self.resolvePath(ipath=state,
                                                  warn=True) # now a share

        if not stateField: #default rules for field
            if state: #state has fields
                if 'value' in state:
                    stateField = 'value'

                else: #ambiguous
                    msg = ("ResolveError: Can't determine field for state"
                          " '{0}'".format(state.name))
                    raise excepting.ResolveError(msg, 'state', self.name,
                                                self.act.human, self.act.count)
            else:
                stateField = 'value'

        if stateField not in state:
            console.profuse("     Warning: Non-existent field '{0}' in state {1}"
                            " ... creating anyway".format(stateField, state.name))
            state[stateField] = 0.0 #create

        parms['stateField'] = stateField

        #convert goal path to share and create field if necessary
        parms['goal'] = goal = self.resolvePath(ipath=goal,
                                                warn=True) # now a share

        if not goalField: #default rules for field
            if goal: #goal has fields
                if 'value' in goal:
                    goalField = 'value'

                else: #use stateField
                    goalField = stateField
            else:
                goalField = 'value'

        if goalField not in goal:
            console.profuse("     Warning: Non-existent field '{0}' in goal"
                    " {1} ... creating anyway".format(goalField, goal.name))
            goal[goalField] = 0.0 #create

        parms['goalField'] = goalField

        return parms #return items are updated in original act parms

    def action(self, state, stateField, comparison, goal, goalField, tolerance, **kwa):
        """ Check if state[field] comparison to goal[goalField] +- tolerance is True
                       parameters:
              state = share of state
              stateField = field key
              comparison
              goal
              goalField
              tolerance

        """

        result = self.Check(state[stateField], comparison, goal[goalField], tolerance)
        console.profuse("Need Indirect, if {0}[{1}] {2} {3}[{4}] +- %s: = {5}\n".format(
            state.name, stateField, comparison, goal, goalField, tolerance, result))

        return result

class NeedMarker(Need):
    """
    NeedMarker is base class for needs that insert markers on resolvelinks
    Special Need

    """
    def resolve(self, share, frame, marker, **kwa):
        """
        Resolves frame name link and then
           inserts marker as first enact in the resolved frame

        parms:
            share       share ref holding mark
            name        name of frame where marker is watching
            frame       only used in resolvelinks
            marker      only used in resolvelinks

        """
        parms = super(NeedMarker, self).resolve( **kwa)

        parms['frame'] = frame = framing.resolveFrame(frame, who=self.name, desc='need marker')
        parms['share'] = share = self.resolvePath(ipath=share,  warn=True) # now a share

        if not share.marks.get(frame.name):
            share.marks[frame.name] = storing.Mark()

        found = False
        for enact in frame.enacts:
            if (isinstance(enact.actor, acting.Actor) and
                    enact.actor.name is marker and
                    enact.parms['share'] is share and
                    enact.parms['name'] == frame.name):
                found = True
                break

        if not found:
            if marker not in acting.Actor.Registry:
                msg = "ResolveError: Bad need marker link"
                raise excepting.ResolveError(msg, marker, self.name,
                                self.act.human, self.act.count)

            markerParms = dict(share=share, frame=frame.name)
            parms['marker'] = marker = acting.Act(  actor=marker,
                                                    registrar=acting.Actor,
                                                    parms=markerParms,
                                                    human=self.act.human,
                                                    count=self.act.count)

            frame.insertEnact(marker)
            console.profuse("     Added {0} {1} with {2} in {3}\n".format(
                'enact',
                marker,
                marker.parms['share'].name,
                marker.parms['frame']))
            marker.resolve()

        return parms #return items are updated in original act parms

    def cloneParms(self, parms, clones, **kw):
        """ Returns parms fixed up for framing cloning. This includes:
            Reverting any Frame links to name strings,
            Reverting non cloned Framer links into name strings
            Replacing any cloned framer links with the cloned name strings from clones
            Replacing any parms that are acts with clones.

            clones is dict whose items keys are original framer names
            and values are duples of (original,clone) framer references
        """
        parms = super(NeedMarker,self).cloneParms(parms, clones, **kw)

        share = parms.get('share')
        name = parms.get('name')
        frame = parms.get('frame')
        marker = parms.get('marker')

        if isinstance(frame, framing.Frame):
            parms['frame'] = frame.name # revert to name

        return parms

class NeedUpdate(NeedMarker):
    """ NeedUpdate Need Special Need """
    def action(self, share, frame, **kw):
        """
        Check if share updated while in frame/mark denoted by name key if any
            Default is False

        parameters:
            share = resolved share that is marked
            frame = resolved frame where marker is placed
            marker = marker kind name
        """
        result = False
        mark = share.marks.get(frame.name) #get mark from mark frame name key
        if mark and mark.stamp is not None and share.stamp is not None:
            result = share.stamp >= mark.stamp #equals so catch updates on enter

        console.profuse("Need Share {0} update in Frame {1} = {2}\n".format(
            share.name, frame.name, result))

        return result

class NeedChange(NeedMarker):
    """NeedChange Need Special Need"""
    def action(self, share, frame, **kw):
        """
        Check if share data changed while in frame/mark denoted by name key if any
            Default is False
        parameters:
            share
            name
            frame       only used in resolvelinks
            marker      only used in resolvelinks
        """
        result = False
        mark = share.marks.get(frame.name) #get mark from mark frame name key
        if mark and mark.data is not None:
            for field, value in share.items():
                try:
                    if getattr(mark.data, field) != value:
                        result = True

                except AttributeError as ex: # new attribute so changed
                    result = True

                if result: #stop checking on first change
                    break


        console.profuse("Need Share {0} change in Frame {1} = {2}\n".format(
            share.name, frame.name, result))

        return result
