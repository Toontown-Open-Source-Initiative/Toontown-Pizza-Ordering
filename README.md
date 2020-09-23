# Toontown-Pizza-Ordering
A feature that allows you to order pizza directly from Toontown

To port this to a Toontown source of your choosing, do the following steps.

Step 1: Get the pizzapi module with your Panda3D's python, then replace the modules included with the ones in the "pizzapi" folder included in this repo

Step 2: Add the localizer strings in TTLocalizerEnglish to your own localizer

Step 3: Instantiate the GUI somewhere and hook it up to a Magic Word or other means in order to load/enter it

Step 4: Enjoy!

Here are some tips you should keep in mind:

 - If you want to do a TEST order, go to line 700 of PizzaGUI and replace the ".place" call with a ".pay_with" call
 - To include closed stores in the pool it chooses a store from, go to line 474 of PizzaGUI and add the argument "closed=True" to the function call
 - Some things in PizzaGUI.py will not be compatible with non-ttoff sources, and I have marked them as such in the code
 - I've made things a *bit* user-friendly, but not 100%. For example, instead of warning you that your subtotal must be 10, it will just crash you when trying to place an order when it isn't. You will also crash when trying to place an order (test or otherwise) if the credit card info doesnt resemble a realistic credit card. For example, you cannot put "a" in the field and expect it to work. The client will also crash if it fails to find a store nearby you to order from.

I will not be supporting this repo, so do not report any crashes or issues or anything like that. I won't see to them. This is just a fun little experiment feature. That's all.

Please, please, PLEASE show me any instances of you ordering a pizza if you decide to actually use this. I find it really hilarious and absolutely want to see all instances of it's use. Just tweet me at @Benjamin8693 or shoot me a message on Discord, Benjamin#8693.

Enjoy your pizza pie :)

P.S. - I know some of the code (especially GUI) is pretty redundant. I got lazy at the end, alright?
