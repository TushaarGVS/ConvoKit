from convokit.hyperconvo.hypergraph import Hypergraph
from typing import List, Dict
from collections import defaultdict
import itertools
from .triadMotif import TriadMotif, MotifType
from convokit.model import Utterance

class TriadMotifExtractor:
    def __init__(self, hypergraph: Hypergraph):
        self.hg = hypergraph

    @staticmethod
    def _sorted_ts(timestamps: List[Utterance]) -> List[Utterance]:
        """
        helper method for getting sorted timestamps of edges between hypernodes, e.g. from Hypergraph.adj_out[C1][C2]
        :param timestamps: e.g. [{'timestamp': 1322706222, 'text': "Lolapalooza"}, {'timestamp': 1322665765, 'text': "Wanda"}]
        :return: edge dictionaries sorted by timestamp
        """
        return sorted(timestamps, key=lambda x: x.timestamp)
        
    def extract_dyadic_motif_counts(self) -> Dict[str, int]:
        motifs = defaultdict(int)
        for C1, C2 in itertools.combinations(self.hg.hypernodes, 2):
            if C1 not in self.hg.adj_in[C2] and C2 not in self.hg.adj_in[C1]:
                motifs['DYADIC[NO_EDGE]'] += 1
            elif C1 in self.hg.adj_in[C2] and C2 in self.hg.adj_in[C1]:
                motifs['DYADIC[TWO_EDGES]'] += 1
            else:
                motifs['DYADIC[ONE_EDGE'] += 1
        return motifs

    def extract_motifs(self) -> Dict[str, List]:

        motifs = dict()

        for motif_type, motif_func in [
            (MotifType.NO_EDGE_TRIADS.name, self.no_edge_triad_motifs),
            (MotifType.SINGLE_EDGE_TRIADS.name, self.single_edge_triad_motifs),
            (MotifType.INCOMING_TRIADS.name, self.incoming_triad_motifs),
            (MotifType.OUTGOING_TRIADS.name, self.outgoing_triad_motifs),
            (MotifType.DYADIC_TRIADS.name, self.dyadic_triad_motifs),
            (MotifType.UNIDIRECTIONAL_TRIADS.name, self.unidirectional_triad_motifs),
            (MotifType.INCOMING_2TO3_TRIADS.name, self.incoming_2to3_triad_motifs),
            (MotifType.INCOMING_1TO3_TRIADS.name, self.incoming_1to3_triad_motifs),
            (MotifType.DIRECTED_CYCLE_TRIADS.name, self.directed_cycle_triad_motifs),
            (MotifType.OUTGOING_3TO1_TRIADS.name, self.outgoing_3to1_triad_motifs),
            (MotifType.INCOMING_RECIPROCAL_TRIADS.name, self.incoming_reciprocal_triad_motifs),
            (MotifType.OUTGOING_RECIPROCAL_TRIADS.name, self.outgoing_reciprocal_motifs),
            (MotifType.DIRECTED_CYCLE_1TO3_TRIADS.name, self.directed_cycle_1to3_triad_motifs),
            (MotifType.DIRECIPROCAL_TRIADS.name, self.direciprocal_triad_motifs),
            (MotifType.DIRECIPROCAL_2TO3_TRIADS.name, self.direciprocal_2to3_triad_motifs),
            (MotifType.TRIRECIPROCAL_TRIADS.name, self.trireciprocal_triad_motifs)
        ]:
            motifs[motif_type] = motif_func()

        return motifs


    # returns list of tuples of form (C1, C2, C3), no edges
    def no_edge_triad_motifs(self):
        motifs = []
        for C1, C2, C3 in itertools.combinations(self.hg.hypernodes, 3):
            if C1 not in self.hg.adj_in[C2] and C1 not in self.hg.adj_in[C3]:
                if C2 not in self.hg.adj_in[C3] and C2 not in self.hg.adj_in[C1]:
                    if C3 not in self.hg.adj_in[C1] and C3 not in self.hg.adj_in[C2]:
                        motifs += [TriadMotif((C1, C2, C3), (), MotifType.NO_EDGE_TRIADS.name)]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2)
    def single_edge_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            incoming = set(self.hg.incoming_hypernodes(C1))
            non_adjacent = set(self.hg.hypernodes) - outgoing.union(incoming)
            outgoing_only = outgoing - incoming

            motifs += [TriadMotif((C1, C2, C3), (self._sorted_ts(self.hg.adj_out[C1][C2]),), MotifType.SINGLE_EDGE_TRIADS.name)
                       for C2 in outgoing_only
                       for C3 in non_adjacent if ((C3 not in self.hg.adj_out[C2]) and (C3 not in self.hg.adj_in[C2]))]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C1)
    def dyadic_triad_motifs(self):
        motifs = []
        for C3 in self.hg.hypernodes: # define the triad with respect to C3 <- prevents double counting
            outgoing = set(self.hg.outgoing_hypernodes(C3))
            incoming = set(self.hg.incoming_hypernodes(C3))
            non_adjacent = set(self.hg.hypernodes) - outgoing.union(incoming)

            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                   self._sorted_ts(self.hg.adj_out[C2][C1])),
                                  MotifType.DYADIC_TRIADS.name)
                       for C1, C2 in itertools.combinations(non_adjacent, 2)
                       if ((C2 in self.hg.adj_out[C1]) and (C1 in self.hg.adj_out[C2]))]
        return motifs


    # returns list of tuples of form (C1, C2, C1->C2, C2->C1) as in paper
    def dyadic_interaction_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            motifs += [(C1, C2, e1, e2) for C2 in self.hg.adj_out[C1] if C2 in
                       self.hg.hypernodes and C1 in self.hg.adj_out[C2]
                       for e1 in self.hg.adj_out[C1][C2]
                       for e2 in self.hg.adj_out[C2][C1]]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C2->C1, C3->C1)
    def incoming_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            incoming_only = incoming - outgoing
            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C2][C1]), self._sorted_ts(self.hg.adj_out[C3][C1])),
                                  MotifType.INCOMING_TRIADS.name)
                       for C2, C3 in itertools.combinations(incoming_only, 2)]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C1->C3)
    def outgoing_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing_only = outgoing - incoming
            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                   self._sorted_ts(self.hg.adj_out[C1][C3])),
                                  MotifType.OUTGOING_TRIADS.name)
                       for C2, C3 in itertools.combinations(outgoing_only, 2)]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C3)
    def unidirectional_triad_motifs(self):
        motifs = []
        for C2 in self.hg.hypernodes: # define the motif with respect to C2
            incoming = set(self.hg.incoming_hypernodes(C2))
            outgoing = set(self.hg.outgoing_hypernodes(C2))
            incoming_only = incoming - outgoing # ignore edges C2->C1
            outgoing_only = outgoing - incoming # ignore edges C3->C2
            for C1 in incoming_only:
                for C3 in outgoing_only:
                    # ensure C3 and C1 have no edges between them
                    if C1 in self.hg.adj_out[C3]: continue
                    if C3 in self.hg.adj_out[C1]: continue
                    motifs += [TriadMotif((C1, C2, C3),
                                          (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                           self._sorted_ts(self.hg.adj_out[C2][C3])),
                                          MotifType.UNIDIRECTIONAL_TRIADS.name)]

        return motifs

    # returns list of tuples of form (C1, C2, C3, C2->C1, C3->C1, C2->C3)
    def incoming_2to3_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            incoming_only = incoming - outgoing # no edges C2->C1
            for C2, C3 in itertools.permutations(incoming_only, 2): # permutations because non-symmetric
                if C2 in self.hg.adj_out[C3]: continue # ensure no C3->C2
                if C3 not in self.hg.adj_out[C2]: continue # ensure C2->C3 exists
                motifs += [TriadMotif((C1, C2, C3),
                                      (self._sorted_ts(self.hg.adj_out[C2][C1]),
                                       self._sorted_ts(self.hg.adj_out[C3][C1]),
                                       self._sorted_ts(self.hg.adj_out[C2][C3])),
                                      MotifType.INCOMING_2TO3_TRIADS.name)
                           ]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C3, C3->C1)
    def directed_cycle_triad_motifs(self):
        # not efficient
        motifs = []
        for C1, C2, C3 in itertools.combinations(self.hg.hypernodes, 3):
            if C3 in self.hg.adj_out[C1]: continue
            if C1 in self.hg.adj_out[C2]: continue
            if C2 in self.hg.adj_out[C3]: continue

            if C2 not in self.hg.adj_out[C1]: continue
            if C3 not in self.hg.adj_out[C2]: continue
            if C1 not in self.hg.adj_out[C3]: continue
            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                   self._sorted_ts(self.hg.adj_out[C2][C3]),
                                   self._sorted_ts(self.hg.adj_out[C3][C1])),
                                  MotifType.DIRECTED_CYCLE_TRIADS.name)]

        return motifs

    # returns list of tuples of form (C1, C2, C3, C2->C1, C3->C1, C1->C3)
    def incoming_1to3_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            for C2, C3 in itertools.permutations(incoming, 2):
                if C2 in self.hg.adj_out[C1]: continue
                if C2 in self.hg.adj_out[C3]: continue
                if C3 in self.hg.adj_out[C2]: continue
                if C3 not in self.hg.adj_out[C1]: continue

                motifs += [TriadMotif((C1, C2, C3),
                                      (self._sorted_ts(self.hg.adj_out[C2][C1]),
                                       self._sorted_ts(self.hg.adj_out[C3][C1]),
                                       self._sorted_ts(self.hg.adj_out[C1][C3])),
                                      MotifType.INCOMING_1TO3_TRIADS.name)
                           ]

        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C1->C3, C3->C1)
    def outgoing_3to1_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            outgoing = self.hg.outgoing_hypernodes(C1)
            for C2, C3 in itertools.permutations(outgoing, 2):
                if C1 in self.hg.adj_out[C2]: continue
                if C2 in self.hg.adj_out[C3]: continue
                if C3 in self.hg.adj_out[C2]: continue

                if C1 not in self.hg.adj_out[C3]: continue
                motifs += [TriadMotif((C1, C2, C3),
                                      (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                       self._sorted_ts(self.hg.adj_out[C1][C3]),
                                       self._sorted_ts(self.hg.adj_out[C3][C1])),
                                      MotifType.OUTGOING_3TO1_TRIADS.name)
                           ]

        return motifs

    # returns list of tuples of form (C1, C2, C3, C2->C1, C3->C1, C2->C3, C3->C2)
    def incoming_reciprocal_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            incoming_only = incoming - outgoing

            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C2][C1]),
                                   self._sorted_ts(self.hg.adj_out[C3][C1]),
                                   self._sorted_ts(self.hg.adj_out[C2][C3]),
                                   self._sorted_ts(self.hg.adj_out[C3][C2])),
                                  MotifType.INCOMING_RECIPROCAL_TRIADS.name)
                       for C2, C3 in itertools.combinations(incoming_only, 2)
                       if ((C3 in self.hg.adj_out[C2]) and (C2 in self.hg.adj_out[C3]))
                       ]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C1->C3, C2->C3, C3->C2)
    def outgoing_reciprocal_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            outgoing_only = outgoing - incoming

            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                   self._sorted_ts(self.hg.adj_out[C1][C3]),
                                   self._sorted_ts(self.hg.adj_out[C2][C3]),
                                   self._sorted_ts(self.hg.adj_out[C3][C2])),
                                  MotifType.OUTGOING_RECIPROCAL_TRIADS.name)
                       for C2, C3 in itertools.combinations(outgoing_only, 2)
                       if ((C3 in self.hg.adj_out[C2]) and (C2 in self.hg.adj_out[C3]))
                       ]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C3, C3->C1, C1->C3)
    def directed_cycle_1to3_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            for C2, C3 in itertools.permutations(outgoing, 2):
                if C1 in self.hg.adj_out[C2]: continue
                if C2 in self.hg.adj_out[C3]: continue

                if C3 not in self.hg.adj_out[C2]: continue
                if C1 not in self.hg.adj_out[C3]: continue

                motifs += [TriadMotif((C1, C2, C3),
                                      (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                       self._sorted_ts(self.hg.adj_out[C2][C3]),
                                       self._sorted_ts(self.hg.adj_out[C3][C1]),
                                       self._sorted_ts(self.hg.adj_out[C1][C3])),
                                      MotifType.DIRECTED_CYCLE_1TO3_TRIADS.name)
                           ]
        # for m in motifs:
        #     print(m)
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C1, C1->C3, C3->C1)
    def direciprocal_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            in_and_out = incoming.intersection(outgoing)
            for C2, C3 in itertools.combinations(in_and_out, 2):
                if C3 in self.hg.adj_out[C2]: continue
                if C2 in self.hg.adj_out[C3]: continue

                motifs += [TriadMotif((C1, C2, C3),
                                      (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                       self._sorted_ts(self.hg.adj_out[C2][C1]),
                                       self._sorted_ts(self.hg.adj_out[C1][C3]),
                                       self._sorted_ts(self.hg.adj_out[C3][C1])),
                                      MotifType.DIRECIPROCAL_TRIADS.name)
                           ]
        return motifs

    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C1, C1->C3, C3->C1, C2->C3)
    def direciprocal_2to3_triad_motifs(self):
        motifs = []
        for C1 in self.hg.hypernodes:
            incoming = set(self.hg.incoming_hypernodes(C1))
            outgoing = set(self.hg.outgoing_hypernodes(C1))
            in_and_out = incoming.intersection(outgoing)
            for C2, C3 in itertools.permutations(in_and_out, 2):
                if C2 in self.hg.adj_out[C3]: continue
                if C3 not in self.hg.adj_out[C2]: continue

                motifs += [TriadMotif((C1, C2, C3),
                                      (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                       self._sorted_ts(self.hg.adj_out[C2][C1]),
                                       self._sorted_ts(self.hg.adj_out[C1][C3]),
                                       self._sorted_ts(self.hg.adj_out[C3][C1]),
                                       self._sorted_ts(self.hg.adj_out[C2][C3])),
                                      MotifType.DIRECIPROCAL_2TO3_TRIADS.name)
                           ]
        return motifs


    # returns list of tuples of form (C1, C2, C3, C1->C2, C2->C1, C2->C3, C3->C2, C3->C1, C1->C3)
    def trireciprocal_triad_motifs(self):
        # prevents triple-counting
        motifs = []
        for C1, C2, C3 in itertools.combinations(self.hg.hypernodes, 3):
            if C2 not in self.hg.adj_out[C1]: continue
            if C1 not in self.hg.adj_out[C2]: continue
            if C3 not in self.hg.adj_out[C2]: continue
            if C2 not in self.hg.adj_out[C3]: continue
            if C1 not in self.hg.adj_out[C3]: continue
            if C3 not in self.hg.adj_out[C1]: continue

            motifs += [TriadMotif((C1, C2, C3),
                                  (self._sorted_ts(self.hg.adj_out[C1][C2]),
                                   self._sorted_ts(self.hg.adj_out[C2][C1]),
                                   self._sorted_ts(self.hg.adj_out[C2][C3]),
                                   self._sorted_ts(self.hg.adj_out[C3][C2]),
                                   self._sorted_ts(self.hg.adj_out[C3][C1]),
                                   self._sorted_ts(self.hg.adj_out[C1][C3])),
                                  MotifType.TRIRECIPROCAL_TRIADS.name)
                       ]

        return motifs
