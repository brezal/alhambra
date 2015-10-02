from tileutils import gettile
import copy

class seed_tileadapts:
    def create_adapter_sequences( self, tileset ):
        tset = copy.deepcopy( tileset )

        for adapter in tset['seed']['adapters']:
            tile_to_mimic = gettile( tset, adapter['tilestrand'][0] )
            
            if tile_to_mimic['type'] == 'tile_daoe_5up':
                # Tile is single. If we have ends, check that they match.
                if ( 'ends' in adapter.keys() ) and ( adapter['ends'] != tile_to_mimic['ends'][1:3] ):
                    raise ValueError("adapter {} and tile base {} ends don't match: adapter has {}, tile has {}".format(
                        adapter['name'], tile_to_mimic['name'], adapter['ends'], tile_to_mimic['ends'][1:3] ))
                adapter_strand_short = tile_to_mimic['fullseqs'][-1]
                tile_long_strand = tile_to_mimic['fullseqs'][-2]
            elif tile_to_mimic['type'] == 'tile_daoe_doublehoriz_35up' \
                    or tile_to_mimic['type'] == 'tile_daoe_doublevert_35up':
                if ( 'ends' in adapter.keys() ) and ( adapter['ends'] != tile_to_mimic['ends'][2:4] ):
                    raise ValueError("adapter {} and tile base {} ends don't match: adapter has {}, tile has {}".format(
                        adapter['name'], tile_to_mimic['name'], adapter['ends'], tile_to_mimic['ends'][1:3] ))
                adapter_strand_short = tile_to_mimic['fullseqs'][-1]
                tile_long_strand = tile_to_mimic['fullseqs'][-2]

            adapter['seqs'] = [ tile_long_strand[0:8]+self.cores[adapter['loc']-1]+tile_long_strand[40:48], 
                                adapter_strand_short ]

        return tset
    
    def create_adapter_sequence_diagram( self, adapterdef ):
        # At the moment, there are only three potential structures, so I'm just
        # going to put them here.
        ttype = 'tile_adapter_5up'
        if 'extra' in adapterdef.keys():
            ttype += '_'+adapterdef['extra']
        
        from lxml import etree
        import pkg_resources
        import os
        base_svg = etree.parse( pkg_resources.resource_stream(__name__, os.path.join('seqdiagrambases',ttype+'.svg') ) )

        s = adapterdef['seqs'][1]
        l = adapterdef['seqs'][0]
        name = adapterdef['name']
        if 'extra' not in adapterdef.keys():
            strings = [(s[0:5]+'--'+s[5:13])[::-1],s[13:21]+'--'+s[21:26], \
                      (l[0:8]+'--'+l[8:16])[::-1],l[16:24][::-1],l[24:32],l[32:40]+'--'+l[40:48], \
                      adapterdef['ends'][0],adapterdef['ends'][1],name]
        elif adapterdef['extra'] == '1h':
            hp = s[0:13]; s = s[13:]
            strings = [hp[0:5]+'-'+hp[5:7]+'-'+hp[7:9], \
                      (hp[9:11]+'-'+hp[11:13]+'-'+s[0:5]+'--'+s[5:13])[::-1],s[13:21]+'--'+s[21:26], \
                      (l[0:8]+'--'+l[8:16])[::-1],l[16:24][::-1],l[24:32],l[32:40]+'--'+l[40:48], \
                      adapterdef['ends'][1],name]
        elif adapterdef['extra'] == '2h':
            strings = [(s[0:5]+'--'+s[5:13])[::-1],s[13:21]+'--'+s[21:26]+'-'+s[26:28]+'-'+s[28:30], \
                      (s[30:32]+'-'+s[32:34]+'-'+s[34:39])[::-1], \
                      (l[0:8]+'--'+l[8:16])[::-1],l[16:24][::-1],l[24:32],l[32:40]+'--'+l[40:48], \
                      adapterdef['ends'][0],name]

        texts = base_svg.findall( "//{http://www.w3.org/2000/svg}text" )

        for text, string in zip(texts,strings):
            text.text = string

        return base_svg.xpath('/svg:svg/svg:g',namespaces={'svg':'http://www.w3.org/2000/svg'})[0]


class longrect(seed_tileadapts):
    cores = ['CAGGAACGGTACGCCATTAAAGGGATTTTAGA',
             'CTACATTTTGACGCTCACGCTCATGGAAATAC',
             'CCAGCAGAAGATAAAAAATACCGAACGAACCA',
             'GCCGTCAATAGATAATCAACTAATAGATTAGA',
             'ACTTCTGAATAATGGATGATTGTTTGGATTAT',
             'GAAGATGATGAAACAAAATTACCTGAGCAAAA',
             'CATAGGTCTGAGAGACGTGAATTTATCAAAAT',
             'GAAAAAGCCTGTTTAGGGAATCATAATTACTA',
             'ACGCGCCTGTTTATCAGTTCAGCTAATGCAGA',
             'GCTTATCCGGTATTCTAAATCAGATATAGAAG',
             'AACGTCAAAAATGAAAAAACGATTTTTTGTTT',
             'GCAGATAGCCGAACAATTTTTAAGAAAAGTAA',
             'AGACAAAAGGGCGACAGGTTTACCAGCGCCAA',
             'GCGTCAGACTGTAGCGATCAAGTTTGCCTTTA',
             'GTCAGACGATTGGCCTCAGGAGGTTGAGGCAG',
             'TGAAAGTATTAAGAGGCTATTATTCTGAAACA']
    
class triangle_side2(seed_tileadapts):
    cores = ['AGAGAGTACCTTTAATCCAACAGGTCAGGATT',
             'TAAGAGGAAGCCCGAAATTGCATCAAAAAGAT',
             'CCCCCTCAAATGCTTTTAAATATTCATTGAAT',
             'TACCAGACGACGATAATATCATAACCCTCGTT',
             'CGTTAATAAAACGAACTGGGAAGAAAAATCTA',
             'TAACAAAGCTGCTCATATTACCCAAATCAACG',
             'ATTGTGTCGAAATCCGTATCATCGCCTGATAA',
             'CGAGGGTAGCAACGGCAAAGACAGCATCGGAA',
             'TCTCCAAAAAAAAGGCTTTTTCACGTTGAAAA',
             'TTTCGTCACCAGTACAGTACCGTAACACTGAG',
             'TCAGTACCAGGCGGATATTAGCGGGGTTTTGC',
             'GATACAGGAGTGTACTATACATGGCTTTTGAT',
             'ACCAGAGCCGCCGCCACGCCACCAGAACCACC',
             'GCGTTTGCCATCTTTTCATAGCCCCCTTATTA',
             'ATGAAACCATCGATAGGCCGGAAACGTCACCA',
             'ATCACCGTCACCGACTTCATTAAAGGTGAATT']

seedtypes = { 'longrect': longrect(), 'triangle_side2': triangle_side2() }
