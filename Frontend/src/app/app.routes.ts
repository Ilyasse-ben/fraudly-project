import { Routes } from '@angular/router';
import { Cours } from './cours/cours';
import { Examen } from './examen/examen';
import { Allcours } from './allcours/allcours';
import { ListEtudientCours } from './list-etudient-cours/list-etudient-cours';
import { Createcours } from './createcours/createcours';
import { Chapiter } from './chapiter/chapiter';
import { DashbordProf } from './dashbord-prof/dashbord-prof';
import { Assistant } from './assistant/assistant';
import { ListExemane } from './list-exemane/list-exemane';
import { Login } from './login/login';

export const routes: Routes = [
    {path:"cours",component:Cours},
    { path: "listexemen", component: ListExemane },
    { path: "Allcours", component: Allcours },
    { path: "listEtudiant", component: ListEtudientCours },
    {path:"createCours", component:Createcours},
    {path:"chapitre",component:Chapiter},
    { path: "dashbord", component: DashbordProf },
    { path: "assistant", component: Assistant },
    { path: "exemen", component: Examen },
    {path:"login", component:Login}


    

];
