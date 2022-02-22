from tkinter.ttk import *
from tkinter import *
from tkinter import messagebox, font
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from scipy.special import expit

import pandas as pd, numpy as np
import rdflib
from ampligraph.evaluation import evaluate_performance
from ampligraph.utils import restore_model

selected = None
lb = None

sub_column = 2
pred_column = 5
obj_column = 8

selected_sub = None
selected_pred = None
selected_obj = None

selected_sub_label = None
selected_pred_label = None
selected_obj_label = None

#Generating listbox in order to show requested values
def listSubjects(item):
    global lb, loadButton

    #disable load_button
    loadButton.configure(state = DISABLED)

    #load subjects, predicates OR objects from csv file
    df = pd.read_csv('HP_uri.csv', names=["subject","relation","object"])
    value = []
    prefix = "http://dbpedia.org/resource/"

    for _,row in df.iterrows(): 
        it = row[item].replace(prefix,'')   #filter prefix in order to show only the local name
        if it not in value:                 #ignore duplicates
            value.append(it)
    value.sort()
    list_items = StringVar(value=value)

    #create listbox to show values
    lb = Listbox(listvariable=list_items)
    #place listbox in different column depending on requested item
    if(item == "subject"):
        lb.grid(row = 3, column = sub_column)
    elif(item == "relation"):
        lb.grid(row = 3, column = pred_column)
    elif(item == "object"):
        lb.grid(row = 3, column = obj_column)

    lb.bind('<<ListboxSelect>>', item_selected)

#Handling listbox selection     
def item_selected(event):
    global lb,selected_sub, selected_pred, selected_obj
    global selected_sub_label, selected_pred_label, selected_obj_label
    global confirmButton
    
    index = lb.curselection()
    selected = lb.get(index) 
    
    if lb.grid_info() :
        x, y = lb.grid_info()["row"], lb.grid_info()["column"]       
        lb.grid_remove()        #remove listbox after selection

        #subject selection
        if y == sub_column:
            if selected_sub_label:
                selected_sub_label.config(text=selected)
            else:
                selected_sub_label = Label(window, text=selected, background = bg_color, font = ("Californian FB", 11), foreground = "white")
                selected_sub_label.grid(row=x,column=y)
            selected_sub = selected
        
        #predicate selection
        elif y == pred_column:
            if selected_pred_label:
                selected_pred_label.config(text=selected)
            else:
                selected_pred_label = Label(window, text=selected, background = bg_color, font = ("Californian FB", 11), foreground = "white")
                selected_pred_label.grid(row=x,column=y)
            selected_pred = selected

        #object selection
        elif y == obj_column:
            if selected_obj_label:
                selected_obj_label.config(text=selected)
            else:
                selected_obj_label = Label(window, text=selected, background = bg_color, font = ("Californian FB", 11), foreground = "white")
                selected_obj_label.grid(row=x,column=y)
            selected_obj = selected
        
        if selected_sub and selected_pred and selected_obj:
            confirmButton.grid(row = 6, column = pred_column)
            confirmButton.configure(state=NORMAL)


def load_triples():
    # create a neo4j backed Graph
    g = rdflib.Graph(store="Neo4j")
    
    # set the configuration to connect to your Neo4j DB 
    theconfig = {'uri': "neo4j://127.0.0.1:7687", 'database': "neo4j", 'auth': {'user': "neo4j", 'pwd': "sas"}}

    g.open(theconfig, create = True) 
    
    filename = askstring('Name', 'Qual è il nome del file di triple?')
    #showinfo('Hello!', 'Hi, {}'.format(name))
    g.load(filename, format="nt")
    print("Done!")

#Evaluating selected triple       
def evaluate():
    global loadButton

    prefix = "http://dbpedia.org/resource/"
    s = prefix + selected_sub
    p = prefix + selected_pred
    o = prefix + selected_obj

    X_unseen = np.array([[s,p,o]])
    filter_triples = np.load('filter_triples.npy', allow_pickle=True)
    model = restore_model(model_name_path = 'HP_Hole')

    unseen_filter = np.array(list({tuple(i) for i in np.vstack((filter_triples, X_unseen))}))
    rank = evaluate_performance(
        X_unseen, 
        model = model, 
        filter_triples=unseen_filter,   # Corruption strategy filter defined above 
        corrupt_side = 's+o',
        use_default_protocol=False, # corrupt subj and obj separately while evaluating
        verbose=True
    )

    scores = model.predict(X_unseen)
    probs = expit(scores)
    answer = messagebox.askquestion ('Result','Probabilità :' + str(probs[0]) + '\nScore :' + str(scores[0]) + '\nRank :' + str(rank[0]) + '.\nVuoi aggiungere questa tripla al grafo?')
    if answer == 'yes':
        add_to_graph()
    
    loadButton.configure(state=NORMAL)
    
#Adding triple to neo4j graph
def add_to_graph():
    # create a neo4j backed Graph
    g = rdflib.Graph(store="Neo4j")
    
    # set the configuration to connect to your Neo4j DB 
    theconfig = {'uri': "neo4j://127.0.0.1:7687", 
                'database': "neo4j", 
                'auth': {'user': "neo4j", 'pwd': "sas"}}

    g.open(theconfig, create = True)    

    resource = rdflib.Namespace("http://dbpedia.org/")

    sub = rdflib.URIRef("http://dbpedia.org/resource#" + selected_sub)
    g.add((sub, rdflib.RDF.type, resource.subject))
    g.add((sub, resource.name, rdflib.Literal(selected_sub)))
    g.add((sub, resource.link, rdflib.Literal("http://dbpedia.org/resource/" + selected_sub)))

    pred = rdflib.URIRef("http://dbpedia.org/" + selected_pred)

    obj = rdflib.URIRef("http://dbpedia.org/resource#" + selected_obj)
    g.add((obj, rdflib.RDF.type, resource.object))
    g.add((obj, resource.name, rdflib.Literal(selected_obj)))
    g.add((obj, resource.link, rdflib.Literal("http://dbpedia.org/resource/" + selected_obj)))

    g.add((sub, pred, obj))
    print("Done!")






#--------------- main ----------------#
bg_color = "orange"

window = Tk()
window.title("TS")
window.geometry("680x700")
window.configure(bg=bg_color)

'''fonts =list(font.families())
fonts.sort()
print(fonts)'''

#Title
titleImg = PhotoImage(file = "title.gif")
titleImg = titleImg.subsample(2,2)
title_label = Label(window, image=titleImg, anchor=NW, border = 0, highlightthickness = 0, bg = bg_color, height = 250).grid(row=0,column=sub_column)

#Subject
subjectImg = PhotoImage(file = "subject.gif")
subjectImg = subjectImg.subsample(3,3)

subject_label = Label(window, image=subjectImg, anchor=W, border = 0, highlightthickness = 0, bg = bg_color).grid(row=1,column=sub_column)

subButtonImg = PhotoImage(file = "sub_button.gif")

subjectButton = Button(window, image=subButtonImg, border = 0, highlightthickness = 0, bg = bg_color, command= lambda: listSubjects('subject'))
subjectButton.grid(row = 2, column = sub_column)

#Predicate
#predicateImg = PhotoImage(file="predicate.gif")
#predicateImg=predicateImg.subsample(7,7)

predicate_label = Label(window, bg=bg_color, width = 30).grid(row=1,column=pred_column)

predButtonImg = PhotoImage(file = "pred_button.gif")

predicateButton=Button(window,image=predButtonImg, border = 0, highlightthickness = 0, bg = bg_color,command= lambda: listSubjects('relation'))
predicateButton.grid(row = 2, column = pred_column)

#Object
objectImg = PhotoImage(file="objects.gif")
objectImg= objectImg.subsample(2,2)

object_label = Label(window,image=objectImg, anchor=E, border = 0, highlightthickness = 0, bg=bg_color).grid(row=1,column=obj_column)

objButtonImg = PhotoImage(file = "obj_button.gif")

objectButton = Button(window, image=objButtonImg, border = 0, highlightthickness = 0, bg = bg_color, command= lambda: listSubjects('object'))
objectButton.grid(row = 2, column = obj_column)

#Confirm Button
evalButtonImg = PhotoImage(file = "eval_button.gif")

confirmButton=Button(window, image=evalButtonImg, border = 0, highlightthickness = 0, bg = bg_color, command=evaluate)

#Load Button
loadButtonImg = PhotoImage(file = "load_button.gif")
loadButton = Button(window, image=loadButtonImg, border = 0, highlightthickness = 0, bg = bg_color, command= load_triples)
loadButton.grid(row = 0, column = obj_column)

while True:
    window.mainloop()
   
            
