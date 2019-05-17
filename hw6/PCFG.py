
# coding: utf-8

import re

def get_grammar(s):
    """
    give a string, find all the grammar rules in the string
    """
    grammar_repo = []
    simple_grammars = re.findall("\([^\(\)]*\)", s)
    # repeat until you cannot find any ( lhs rhs ) grammar
    while len(simple_grammars) > 0:
        # add all simple grammar into grammar repository
        # replace them with their head
        for simple_grammar in simple_grammars:
            grammar = simple_grammar.split(" ")
            # '(' == grammar[0] and ')' == grammar[-1]
            lhs = grammar[1]
            rhs = grammar[2:-1]
            grammar_repo.append([lhs, rhs])

            s = s.replace(simple_grammar, lhs)

        simple_grammars = re.findall("\([^\(\)]*\)", s)
    return grammar_repo


train_file = "data/train_data.txt"
contents = []
with open(train_file) as f:
    for line in f:
        contents.append(line.strip())


train_grammar = []
for s in contents:
    train_grammar += get_grammar(s)#从train data得到grammar


class PCFG():
    def __init__(self):
        self.grammer = []
        
    def count_grammer(self,train_grammar):
        # 删除train_grammar中重复的grammar
        # 只留下unique grammar
        g_count_list = []
        for g in train_grammar:
            if g not in self.grammer:
                g_count = train_grammar.count(g)
                g_count_list.append(g+[g_count])
                self.grammer.append(g)
        
        # 计算grammar 左边non-terminals的频度
        left_tokens = [g[0] for g in train_grammar]
        left = {}
        already = []
        for token in left_tokens:
            if token not in already:
                left[token] = left_tokens.count(token)
                already.append(token)
        
        # 计算grammar频率
        for g in g_count_list:
            g[2] = 1.0 * g[2]/left[g[0]]

        # LHS相同的，按照频率从小到大排
        sorted_g_list = []
        for token in left.keys():
            cur_g_list = []
            for g in g_count_list:
                if token == g[0]:
                    cur_g_list.append(g)
            cur_g_list = sorted(cur_g_list,key = lambda x:x[2])
            sorted_g_list += cur_g_list
        return sorted_g_list
    
    def parse(self,sentence,grammars):
        """
        parse sentence with the CYK algorithm
        """
        s_arr = sentence.lower().split(" ")
        s_len = len(s_arr)
        d = {}
        for level in range(s_len):
            cur_gap = level
            for span_start in range(s_len-level):
                span_stop = span_start + cur_gap
                cur_span = str(span_start)+"-"+str(span_stop)
                d[cur_span] = []
                if(level == 0): 
                    # 加入所有的lexical rule
                    for g in grammars:
                        if len(g[1]) == 1 and s_arr[span_start] == g[1][0]:
                            d[cur_span].append([g[0],g[2],s_arr[span_start],cur_span,g])
                else:
                    for span_split in range(span_start,span_stop):
                        left_span = str(span_start)+"-"+str(span_split)
                        right_span = str(span_split+1)+"-"+str(span_stop)
                        if left_span in d.keys() and right_span in d.keys():
                            left_index = 0
                            right_index = 0
                            for left_child in d[left_span]:
                                for right_child in d[right_span]:
                                    for g in grammars:
                                        if len(g[1]) == 2 and left_child[0] == g[1][0] and right_child[0] == g[1][1]:
                                            inner_prob = g[2]*left_child[1]*right_child[1] # hyperedge * left * right
                                            d[cur_span].append([g[0],inner_prob,[left_span,left_index],[right_span,right_index],cur_span,g])
                                    right_index += 1
                                left_index += 1
        return d
    
    def find_max_parser(self,sentence,d):
        """
        find the most likely tree
        """
        s_len = len(sentence.lower().split(" "))
        final_span = "0-"+str(s_len-1)
        root = [0,0]
        for root_candidate in d[final_span]:
            if root_candidate[1] > root[1]:
                root = root_candidate
        prob = root[1]
        parser_nodes = [root]
        to_expand = [root]
        while len(to_expand) != 0:
            cur_node = to_expand.pop(0)
            cur_node_index = parser_nodes.index(cur_node)
            if type(cur_node[3]) is not str:
                left = d[cur_node[2][0]][cur_node[2][1]]
                right = d[cur_node[3][0]][cur_node[3][1]]
                to_expand.insert(0,right)
                to_expand.insert(0,left)
                parser_nodes.insert(cur_node_index ,"(")
                parser_nodes.insert(cur_node_index + 2, left )
                parser_nodes.insert(cur_node_index + 3, right)
                parser_nodes.insert(cur_node_index + 4, ")")
            else:
                parser_nodes.insert(cur_node_index , "(")
                parser_nodes.insert(cur_node_index + 2, cur_node[2])
                parser_nodes.insert(cur_node_index + 3, ")")
        parser_str_arr = []
        for node in parser_nodes:
            if type(node) is str:
                parser_str_arr.append(node)
            else:
                parser_str_arr.append(node[0])
            parser_str_arr.append(" ")
        parser_str = "".join(parser_str_arr)
        return parser_str,parser_nodes,prob
    
    def inner(self,sentence,d):
        """
        inside probability
        """
        inner = {}
        s_len = len(sentence.lower().split(" "))
        for level in range(s_len):
            for span_start in range(s_len - level):
                span_stop = span_start + level
                cur_span = str(span_start) + "-" + str(span_stop)
                cur_span_nodes = d[cur_span]
                if len(cur_span_nodes) != 0:
                    inner[cur_span] = {}
                    for node in cur_span_nodes:
                        if node[0] not in inner[cur_span].keys():
                            inner[cur_span][node[0]] = node[1]
                        else:
                            inner[cur_span][node[0]] += node[1]
        return inner

    def outer(self,sentence,d_s):
        """
        outside probability
        """
        outer = {}
        s_len = len(sentence.lower().split(" "))
        for level in range(s_len-1,-1,-1):
            for span_start in range(s_len - level):
                span_stop = span_start + level
                cur_span = str(span_start) + "-" + str(span_stop)
                cur_span_nodes = d_s[cur_span]
                if len(cur_span_nodes) != 0:
                    outer[cur_span] = {}
                    if level == s_len-1:
                        outer[cur_span]["S"]=1.0
                        for index in range(len(cur_span_nodes)):
                            d_s[cur_span][index].append(1.0)
                    else:
                        for node in cur_span_nodes:
                            if type(node[-1]) is not list:
                                if node[0] not in outer[cur_span].keys():
                                    outer[cur_span][node[0]] = node[-1]
                                else:
                                    outer[cur_span][node[0]] += node[-1]
                    if level != 0:
                        for node in cur_span_nodes:
                            if type(node[-1]) is not list:
                                cur_tag = node[0]
                                left_child = node[2]
                                left_child_in = d_s[left_child[0]][left_child[1]][1]
                                right_child = node[3]
                                right_child_in = d_s[right_child[0]][right_child[1]][1]
                                g = node[5]
                                parent_out_prob = outer[cur_span][cur_tag]
                                g_prob = g[2]
                                left_child_out = parent_out_prob * left_child_in * g_prob
                                right_child_out = parent_out_prob * right_child_in * g_prob
                                d_s[left_child[0]][left_child[1]].append(left_child_out)
                                d_s[right_child[0]][right_child[1]].append(right_child_out)
        return outer,d_s


# ### 1. Train a PCFG
# 根据题目给出的两棵句法树写出PCFG的规则，包括phrasal rule和lexical rule。

pcfg = PCFG()


sorted_grammar = pcfg.count_grammer(train_grammar)


# 输出文件modelFile
# 
# 先输出终结符的grammar 再输出非终结符的grammar

model_file = "data/modelFile"
with open(model_file,"w") as f:
    for g in sorted_grammar:
        # tag # word # prob
        if len(g[1]) == 1:
            f.write(g[0]+" # "+" ".join(g[1])+" # "+str(g[2])+"\n")
    for g in sorted_grammar:
        # LHS # RHS # prob
        if len(g[1]) > 1:
            f.write(g[0]+" # "+" ".join(g[1])+" # "+str(g[2])+"\n")


# ### 2. Find the most likely parse
# a boy with a telescope saw a girl

s = "a boy with a telescope saw a girl"
# ( S ( NP ( NP ( DT a ) ( NN boy ) ) ( PP ( IN with ) ( NP ( DT a ) ( NN telescope ) ) ) ) ( VP ( VBD saw ) ( NP ( DT a ) ( NN girl ) ) ) ) '
d_s = pcfg.parse(s,sorted_grammar)


s_parser, parser_nodes, prob = pcfg.find_max_parser(s,d_s)


# ### 3. Calculate the inside and outside log probabilities for all spans and labels

pcfg = PCFG()
d_inner = pcfg.inner(s,d_s)
d_outer, d_s = pcfg.outer(s,d_s)


# 输出文件parseFile

import numpy as np
def log(prob):
    return "%.6f" % np.log10(prob)

def output(s,prob,s_parser,d_inner,d_outer,model_file):
    with open (model_file,"w") as f:
        # the most likely parse in the bracketed form
        f.write(s_parser + "\n")
        # the highest probability
        f.write(log(prob) + "\n")
        s_n = len(s.split(" "))
        for level in range(s_n):
            for span_start in range(s_n - level):  # # 0,1,...,s_n-level-1
                span_stop = span_start + level
                cur_span = str(span_start) + "-" + str(span_stop)  # 0-1"
                if cur_span in d_inner.keys():
                    for node in d_inner[cur_span].items():
                        cur_tag = node[0]
                        inprob = d_inner[cur_span][cur_tag]
                        if cur_tag not in d_outer[cur_span].keys():
                            outprob = 0.0
                        else:
                            outprob = d_outer[cur_span][cur_tag]
                        # Nj # p # q # betaj(p,q) # alphaj(p,q)
                        f.write(cur_tag +" # " + str(span_start) +" # " + str(span_stop) +" # " + log(inprob) +" # " + log(outprob) + '\n')


parser_file = "data/parseFile"
output(s,prob,s_parser,d_inner,d_outer,parser_file)

