# Description

Anki add-on to import exported decks from [Flashcards Deluxe](http://flashcardsdeluxe.com).

It preserves due dates for cards, turns text in &lt;b&gt; or &lt;u&lt; tags
into Cloze cards, and maps from categories to tags during import. It can also
add an additional set of tags to all cards imported.

# Requirements

- "Basic (and reversed card)" model
- "Cloze" model
- Flashcards Deluxe deck exported as "Basic Text" with statistics
- deck has columns: Text 1, Text 2, Text 3, Category 1, Category 2, Statistics 1
- [Add Note ID](https://ankiweb.net/shared/info/1672832404) add-on installed

To customize the category-to-tag mapping, create a CSV file mapping the
Category 1 and Category 2 columns of your Flashcards Deluxe deck to the Anki
tags you want. The CSV file should put all values in double quotes, and use tabs
to separate the two columns.

# Support

This add-on is considered **alpha quality**: it works for me and you should give
it a try, but your setup needs to be very similar to mine. And back up your Anki
database first!

Post a
[new issue on Github](https://github.com/Arthaey/anki-flashcards-deluxe-importer/issues/new)
(or make a pull request!). You can also write a review or ask questions on the
[Anki website for shared add-ons](https://ankiweb.net/shared/info/1356674785).

[My other Anki add-ons](https://github.com/search?q=user%3AArthaey+anki)
are also on Github.

# TODO:

- dynamically determine the number of fields for the model
- check whether the Note Id addon is actually in use
- UI for users to configure add-on without editing the code

# License

This addon is licensed under the same license as Anki itself (GNU Affero General
Public License 3).
