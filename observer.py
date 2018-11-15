"""
Implementation of observer pattern from 'Design Patterns - Elements Of Reusable Object-Oriented Software'
by Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides - The 'Gang Of Four'
"""

from abc import ABC, abstractmethod

class AbstractObservable(ABC):

    @abstractmethod
    def addObserver(self,observer):
        pass
    @abstractmethod
    def removeObserver(self, observer):
        pass
    @abstractmethod
    def notify(self):
        pass

class AbstractObserver(ABC):

    @abstractmethod
    def objectChanged(self, data):
        pass

class Observable(AbstractObservable):
    def __init__(self):
        self._observers = set()

    def addObserver(self, observer):
        self._observers.add(observer)

    def removeObserver(self, observer):
        try:
            self._observers.remove(observer)
        except:
            print(f'{self._observers} does not contain {observer} so cannot remove it')

    def notify(self, data):
        for o in self._observers:
            o.objectChanged(data)
