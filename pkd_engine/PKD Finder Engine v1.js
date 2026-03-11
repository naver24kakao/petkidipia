/*
File: pkd_finder_engine_260310.js
Project: Petkidipia
Purpose: Breed Finder Engine
Input: pkd_runtime_bundle_scored.json
Output: Filtered breed cards
Author: Grid
*/

class PKDFinderEngine {

constructor(){
this.data = []
this.filtered = []
this.filters = {}
this.search = ""
}

/* ===============================
BOOT
=============================== */

async pkd_boot(path){

const res = await fetch(path)
this.data = await res.json()

this.filtered = this.data

this.pkd_bind_search()
this.pkd_bind_filters()

this.pkd_render()

}

/* ===============================
SEARCH
=============================== */

pkd_bind_search(){

const input = document.querySelector("[data-pkd-search]")

if(!input) return

input.addEventListener("input",(e)=>{

this.search = e.target.value.toLowerCase()

this.pkd_apply_filters()

})

}

/* ===============================
FILTER
=============================== */

pkd_bind_filters(){

const buttons = document.querySelectorAll("[data-pkd-filter]")

buttons.forEach(btn=>{

btn.addEventListener("click",()=>{

const key = btn.dataset.pkdFilter
const value = btn.dataset.value

this.filters[key] = value

this.pkd_apply_filters()

})

})

}

/* ===============================
FILTER APPLY
=============================== */

pkd_apply_filters(){

this.filtered = this.data.filter(breed=>{

/* search */

if(this.search){

const name = breed.breed_ko.toLowerCase()

if(!name.includes(this.search)) return false

}

/* filters */

for(const key in this.filters){

if(breed[key] !== this.filters[key]){

return false

}

}

return true

})

this.pkd_render()

}

/* ===============================
RENDER
=============================== */

pkd_render(){

const container = document.querySelector("[data-pkd-card-container]")

if(!container) return

container.innerHTML = ""

this.filtered.forEach(breed=>{

const card = this.pkd_render_breed_card(breed)

container.appendChild(card)

})

}

/* ===============================
CARD
=============================== */

pkd_render_breed_card(breed){

const card = document.createElement("div")

card.className = "breed-card"

card.innerHTML = `

<img src="/images/breeds/${breed.slug}.jpg">

<h3>${breed.breed_ko}</h3>

<p>${breed.temperament?.join(", ") || ""}</p>

<div>

Shedding: ${breed.shedding}

<br>

Apartment: ${breed.apartment}

</div>

`

card.addEventListener("click",()=>{

window.location.href = "/breeds/"+breed.slug+".html"

})

return card

}

}

/* ===============================
EXPORT
=============================== */

window.PKDFinderEngine = PKDFinderEngine

