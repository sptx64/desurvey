import numpy as np
import streamlit as st

def desurveying(collars, dh, survey=None, survey_is_in="collars", #or dh or desurvey
                desurvey_method="by holeid", #or by fromto
                collars_x="x", collars_y="y", collars_elevation="elevation",
                dh_x="x", dh_y="y", dh_elevation="elevation",
                depth_from="from", depth_to="to", azi="azimuth", dip="dip",
                dip_vertical="negative", concession="concession", holeid="holeid") :

    len_collars=0 if collars is None else len(collars)
    len_survey=0 if survey is None else len(survey)


    # switching to negative dip
    if dip_vertical=="positive" :
        if survey_is_in=="collars" :
            collars.loc[:,dip]= -1*collars["dip"].values
        if survey_is_in=="dh" :
            dh.loc[:,dip]= -1*dh["dip"].values
        if survey_is_in=="survey" :
            survey.loc[:,dip]= -1*dh["dip"].values

    #no merge needed :
    if (collars is None) and (survey is None) :
        dh=dh[[concession, dh_x, dh_y, dh_elevation, holeid, depth_from, depth_to, azi, dip]]
        dh=dh.rename(columns={collars_x:"x", collars_y:"y", collars_elevation:"elevation", concession:"concession", holeid:"holeid", depth_from:"from", depth_to:"to", azi:"azi", dip:"dip"})

    #need merging :
    else :
        kc = [concession, holeid, depth_from, depth_to] #potential key columns for the merge

        #if survey is assigned, survey data are in survey
        if (len_survey>0) & (survey_is_in == "survey") :
            # one survey by holeid
            if desurvey_method == "by holeid" :
                kc = [x for x in kc[:2] if (x != None) & (x in collars) & (x in dh) & (x in desurvey)] #from and to are excluded
                collars,survey,dh = collars[kc+[collars_x,collars_y,collars_elevation]], survey[kc+[azi, dip]], dh[kc + [depth_from, depth_to]]
                collars=collars.merge(survey, on=kc, how="left")
                dh=dh.merge(collars, on=kc, how="left")
                dh=dh.rename(columns={collars_x:"x", collars_y:"y", collars_elevation:"elevation", concession:"concession", holeid:"holeid", depth_from:"from", depth_to:"to", azi:"azi", dip:"dip"})

            # one survey by from to
            elif desurvey_method == "by fromto" :
                kc_dh_desurv = [x for x in kc if (x != None) & (x in dh) & (x in survey)]
                dh,survey = dh[kc_dh_desurv],survey[kc_dh_desurv+[azi, dip]]

                #merge dh col for x,y,z coordinates:
                if collars != None :
                    kc_col_dh = [x for x in kc if (x != None) & (x in dh) & (x in collars)]
                    collars=collars[kc+[collars_x, collars_y, collars_elevation]]
                    dh=dh.merge(collars, on=kc_col_dh, how="left")
                    dh=dh.rename(columns={collars_x:"x", collars_y:"y", collars_elevation:"elevation", concession:"concession", holeid:"holeid", depth_from:"from", depth_to:"to", azi:"azi", dip:"dip"})

                #merge dh and survey:
                dh=dh.merge(survey, on=kc_dh_survey, how="left")

        #implied that desurvey_method = holeid and survey isin collars
        elif (len_collars > 0) & (survey_is_in=="collars") :
            kc = [x for x in kc if (x != None) & (x in collars) & (x in dh)]
            collars,dh = collars[kc+[collars_x,collars_y,collars_elevation, azi, dip]], dh[kc + [depth_from, depth_to]]
            dh=dh.merge(collars, on=kc, how='left')
            dh=dh.rename(columns={collars_x:"x", collars_y:"y", collars_elevation:"elevation", concession:"concession", holeid:"holeid", depth_from:"from", depth_to:"to", azi:"azi", dip:"dip"})

        #implied that desurvey_method = fromto and survey is in dh already
        elif (len_collars>0) & (survey_is_in=="collars") :
            kc = [x for x in kc if (x != None) & (x in collars) & (x in dh)]
            collars,dh=collars[kc+[collars_x,collars_y,collars_elevation]],dh[kc + [depth_from, depth_to, azi, dip]]
            dh=dh.merge(collars, on=kc, how='left')
            dh=dh.rename(columns={collars_x:"x", collars_y:"y", collars_elevation:"elevation", concession:"concession", holeid:"holeid", depth_from:"from", depth_to:"to", azi:"azi", dip:"dip"})



    dh["key"]=[f"{conc}_{hid}" for conc,hid in zip(dh["concession"].values, dh["holeid"].values)] if "concession" in dh else dh["holeid"].values
    keys, x, y, elev, azi, dip, depth_from, depth_to = dh["key"].values, dh["x"].values, dh["y"].values, dh["elevation"].values, dh["azi"].values, dh["dip"].values, dh["from"].values, dh["to"].values

    azi=np.array([np.deg2rad(90. - a) for a in azi])
    dip=np.array([np.deg2rad(d) for d in dip])

    k, xfrom, xto, yfrom, yto, zfrom, zto=[], [], [], [], [], [], []

    for key in np.unique(keys) :
        cond = keys == key
        x_key, y_key, elev_key=x[cond], y[cond], elev[cond]
        azi_key, dip_key, from_key, to_key=azi[cond], dip[cond], depth_from[cond], depth_to[cond]
        for i in range(len(x_key)) :
            azi_i, dip_i = azi_key[i], dip_key[i]
            vector = np.array([np.cos(azi_i)*np.cos(dip_i), np.sin(azi_i)*np.cos(dip_i), np.sin(dip_i)])

            if i==0 :
                xfrom.append(x_key[i])
                yfrom.append(y_key[i])
                zfrom.append(elev_key[i])
            else :
                xfrom.append(xto[-1])
                yfrom.append(yto[-1])
                zfrom.append(zto[-1])

            depth=to_key[i]-from_key[i]
            xto.append(xfrom[-1] + depth*vector[0])
            yto.append(yfrom[-1] + depth*vector[1])
            zto.append(zfrom[-1] + depth*vector[2])

            k.append(key)

    return xfrom,yfrom,zfrom,xto,yto,zto
