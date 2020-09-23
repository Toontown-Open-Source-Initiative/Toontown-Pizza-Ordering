from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

from libotp import WhisperPopup

from panda3d.core import *

from pizzapi import *

from toontown.battle import Fanfare
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

import random

DEAL_CODE = 0
DEAL_DESC = 1

BUTTON_BROWSE = 0
BUTTON_ADDRESS = 1
BUTTON_CLOSE = 2

INFO_COUNT = 4

STAGE_NAME = 0
STAGE_ADDRESS = 1
STAGE_CARD = 2
STAGE_FINAL = 3

ITEM_CODE = 0
ITEM_NAME = 1
ITEM_PRICE = 2


class PizzaGUI(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('PizzaGUI')

    def __init__(self):
        DirectFrame.__init__(self, parent=aspect2d, relief=None, image=DGG.getDefaultDialogGeom(), pos=(0.0, 0.0, 0.05),
                             image_scale=(1.8, 1, 1.4), image_pos=(0, 0, -0.05), image_color=ToontownGlobals.GlobalDialogColor,
                             text=TTLocalizer.PizzaMenuTitle, text_scale=0.12, text_pos=(0, 0.5), borderWidth=(0.01, 0.01))
        StateData.StateData.__init__(self, 'pizza-gui-done')

        self.setBin('gui-popup', 0)
        self.initialiseoptions(PizzaGUI)

        # These help us keep track of whether we have loaded/entered the interface
        self.isLoaded = 0
        self.isEntered = 0

        # Some nice music to play when our menu is open
        self.music = base.loader.loadMusic('phase_14.5/audio/bgm/PP_theme.ogg')

        # Sound effects for success and failure
        self.successSfx = base.loader.loadSfx('phase_3.5/audio/sfx/tt_s_gui_sbk_cdrSuccess.ogg')
        self.failureSfx = base.loader.loadSfx('phase_3.5/audio/sfx/tt_s_gui_sbk_cdrFailure.ogg')
        self.purchaseSfx = base.loader.loadSfx('phase_14/audio/sfx/cash.ogg')

        # Non-GUI Info
        self.infoState = STAGE_NAME
        self.customer = None
        self.address = None
        self.card = None
        self.store = None
        self.menu = None
        self.productId = None
        self.cart = []
        self.activeDeals = []

        # Used between multiple screens
        self.logo = None
        self.infoLabel = None

        # The information submission screen
        self.infoNode = None
        self.entryLabels = []
        self.entryFrames = []
        self.entryInputs = []
        self.submitButton = None

        # The title screen
        self.titleNode = None
        self.menuButtons = []
        self.dealButton = None

        # Menu screen
        self.menuNode = None
        self.menuEntryFrame = None
        self.menuEntryInput = None
        self.checkoutButton = None
        self.addButton = None
        self.menuList = None
        self.productLabel = None
        self.backButton = None

        # Checkout screen
        self.checkoutNode = None
        self.backToMenuButton = None
        self.removeButton = None
        self.placeOrderButton = None
        self.cartList = None
        self.cartProductLabel = None
        self.totalsLabel = None

    def unload(self):
        # Only unload if we have the interface loaded
        if not self.isLoaded:
            return
        self.isLoaded = False

        # Exit the interface
        self.exit()

        # Unload the DirectFrame
        DirectFrame.destroy(self)

    def load(self):
        # Only load if we haven't yet loaded
        if self.isLoaded:
            return
        self.isLoaded = True

        # Load the Domino's Pizza logo as a texture
        logoTexture = loader.loadTexture('phase_14.5/maps/pp_logo.jpg', 'phase_14.5/maps/pp_logo_a.rgb')
        self.logo = OnscreenImage(image=logoTexture)
        self.logo.setTransparency(TransparencyAttrib.MAlpha)
        self.logo.setScale(0.25)
        self.logo.setPos(-0.35, 0, 0)
        self.logo.reparentTo(self)

        # A general label we use to display information
        self.infoLabel = DirectLabel(parent=self, relief=None, pos=(-0.35, 0.0, -0.55), scale=0.1, text=TTLocalizer.PizzaInfoNameEntry,
                                     text_font=ToontownGlobals.getInterfaceFont())

        # We use this node for our information submission screen
        self.infoNode = self.attachNewNode('infoNode')

        # Generate entry boxes to put info into
        model = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        for x in range(INFO_COUNT):
            # Get the label text and position for this entry box
            text = TTLocalizer.PizzaEntryName[x]
            z = (-0.25 * (x + 1)) + 0.5

            # A label that goes above the entry box
            entryInfo = DirectLabel(parent=self.infoNode, relief=None, pos=(0.4, 0.0, z + 0.1), scale=0.07, text=text,
                                    text_font=ToontownGlobals.getInterfaceFont())
            self.entryLabels.append(entryInfo)

            # The entry box GUI
            entryFrame = DirectFrame(parent=self.infoNode, relief=None, image=model.find('**/tt_t_gui_sbk_cdrCodeBox'),
                                     pos=(0.4, 0.0, z), scale=0.6)
            self.entryFrames.append(entryFrame)

            # A DirectEntry to input information
            entryInput = DirectEntry(parent=self.infoNode, relief=None, text_scale=0.035, width=11.5,
                                     textMayChange=1, pos=(0.2, 0.0, z), text_align=TextNode.ALeft,
                                     backgroundFocus=0, focusInCommand=self.toggleEntryFocus,
                                     focusInExtraArgs=[True], focusOutCommand=self.toggleEntryFocus,
                                     focusOutExtraArgs=[False])
            self.entryInputs.append(entryInput)
        model.removeNode()

        # This button submits the info we entered in the entry boxes
        model = loader.loadModel('phase_3/models/gui/quit_button')
        self.submitButton = DirectButton(parent=self.infoNode, relief=None, scale=1, pos=(-0.35, 0.0, -0.65),
                                         image=(model.find('**/QuitBtn_UP'), model.find('**/QuitBtn_DN'), model.find('**/QuitBtn_RLVR')),
                                         image_scale=(1.25, 1, 1), text=TTLocalizer.PizzaInfoSubmit, text_scale=0.05,
                                         text_pos=TTLocalizer.DSDcancelPos, command=self.submitInformation)
        model.removeNode()

        # We use this node for our menu's title screen
        self.titleNode = self.attachNewNode('titleNode')

        model = loader.loadModel('phase_3/models/gui/quit_button')
        for x in range(len(TTLocalizer.PizzaButtons)):
            text = TTLocalizer.PizzaButtons[x]
            z = (-0.2 * (x + 1)) + 0.4
            button = DirectButton(parent=self.titleNode, relief=None, scale=1.25, pos=(0.45, 0.0, z), image=(model.find('**/QuitBtn_UP'),
                                                                                                             model.find('**/QuitBtn_DN'),
                                                                                                             model.find('**/QuitBtn_RLVR')),
                                  image_scale=(1.25, 1, 1), text=text, text_scale=0.05,
                                  text_pos=TTLocalizer.DSDcancelPos, command=self.selectOption, extraArgs=[x])
            self.menuButtons.append(button)
        model.removeNode()

        # Create a button that you can click to automatically add a daily deal to your cart
        self.dealButton = DirectButton(parent=self.titleNode, relief=None, pos=(0.0, 0, -0.65), scale=0.05, text=TTLocalizer.PizzaNoCoupon,
                                       text_font=ToontownGlobals.getInterfaceFont(), text_align=TextNode.ACenter,
                                       command=self.selectDeal, extraArgs=[])

        # Left side clip plane
        leftClip = PlaneNode("left-clip", Plane(Vec3(1.0, 0.0, 0.0), Point3()))
        leftClip.setClipEffect(1)
        leftClipNode = self.titleNode.attachNewNode(leftClip)
        leftClipNode.setX(-0.8)
        self.dealButton.setClipPlane(leftClipNode)

        # Right side clip plane
        rightClip = PlaneNode("right-clip", Plane(Vec3(-1.0, 0.0, 0.0), Point3()))
        rightClip.setClipEffect(1)
        rightClipNode = self.titleNode.attachNewNode(rightClip)
        rightClipNode.setX(0.8)
        self.dealButton.setClipPlane(rightClipNode)

        # Second to last, a node for our simple menu
        self.menuNode = self.attachNewNode('menuNode')

        # We need a box to search for products with
        model = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        self.menuEntryFrame = DirectFrame(parent=self.menuNode, relief=None, image=model.find('**/tt_t_gui_sbk_cdrCodeBox'),
                                          pos=(-0.35, 0.0, 0.175), scale=0.6)
        self.menuEntryInput = DirectEntry(parent=self.menuNode, relief=None, text_scale=0.035, width=11.5,
                                          textMayChange=1, pos=(-0.55, 0.0, 0.175), text_align=TextNode.ALeft,
                                          backgroundFocus=0, focusInCommand=self.toggleEntryFocus,
                                          focusInExtraArgs=[True], focusOutCommand=self.toggleEntryFocus,
                                          focusOutExtraArgs=[False], command=self.menuSearch)
        model.removeNode()

        # These buttons allow you to add items to your cart and go to checkout
        model = loader.loadModel('phase_3/models/gui/quit_button')
        self.checkoutButton = DirectButton(parent=self.menuNode, relief=None, scale=1, pos=(0.45, 0.0, -0.65),
                                           image=(model.find('**/QuitBtn_UP'), model.find('**/QuitBtn_DN'), model.find('**/QuitBtn_RLVR')),
                                           image_scale=(1.25, 1, 1), text=TTLocalizer.PizzaInfoCheckout, text_scale=0.05,
                                           text_pos=TTLocalizer.DSDcancelPos, command=self.checkout)
        self.addButton = DirectButton(parent=self.menuNode, relief=None, scale=1, pos=(-0.35, 0.0, -0.55),
                                      image=(model.find('**/QuitBtn_UP'), model.find('**/QuitBtn_DN'), model.find('**/QuitBtn_RLVR')),
                                      image_scale=(1.25, 1, 1), text=TTLocalizer.PizzaInfoSelect, text_scale=0.05,
                                      text_pos=TTLocalizer.DSDcancelPos, command=self.selectItem)
        model.removeNode()

        # The actual list of items in our menu
        model = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.menuList = DirectScrolledList(parent=self.menuNode, relief=None, forceHeight=0.07, pos=(0.45, 0, -0.05),
                                           incButton_image=(model.find('**/FndsLst_ScrollUp'),
                                                            model.find('**/FndsLst_ScrollDN'),
                                                            model.find('**/FndsLst_ScrollUp_Rllvr'),
                                                            model.find('**/FndsLst_ScrollUp')), incButton_relief=None,
                                           incButton_scale=(1.3, 1.3, -1.3), incButton_pos=(0.0, 0, -0.5),
                                           incButton_image3_color=Vec4(1, 1, 1, 0.2),
                                           decButton_image=(model.find('**/FndsLst_ScrollUp'),
                                                            model.find('**/FndsLst_ScrollDN'),
                                                            model.find('**/FndsLst_ScrollUp_Rllvr'),
                                                            model.find('**/FndsLst_ScrollUp')), decButton_relief=None,
                                           decButton_scale=(1.3, 1.3, 1.3), decButton_pos=(0.0, 0, 0.47),
                                           decButton_image3_color=Vec4(1, 1, 1, 0.2), itemFrame_pos=(-0.237, 0, 0.41),
                                           itemFrame_scale=1.0, itemFrame_relief=DGG.SUNKEN,
                                           itemFrame_frameSize=(-0.05, 0.56, -0.87, 0.02), itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                           itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=12,
                                           items=[])
        model.removeNode()

        # This label shows product information
        self.productLabel = DirectLabel(parent=self.menuNode, relief=None, pos=(-0.35, 0.0, -0.1), scale=0.075, text='',
                                        text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=12)

        # A button that allows us to go back to the title screen
        model = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        image = [model.find('**/tt_t_gui_mat_shuffleArrow' + name) for name in ('Up', 'Down', 'Up', 'Disabled')]
        self.backButton = DirectButton(self.menuNode, relief=None, image=image,
                                       pos=(-0.965, 0.0, 0.0), command=self.closeMenu)
        model.removeNode()

        # And finally, a node for the checkout screen
        self.checkoutNode = self.attachNewNode('checkoutNode')

        # A button that allows us to go back to the menu
        model = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        image = [model.find('**/tt_t_gui_mat_shuffleArrow' + name) for name in ('Up', 'Down', 'Up', 'Disabled')]
        self.backToMenuButton = DirectButton(self.checkoutNode, relief=None, image=image,
                                             pos=(-0.965, 0.0, 0.0), command=self.returnToCheckout)
        model.removeNode()

        # A remove from cart and place order button
        model = loader.loadModel('phase_3/models/gui/quit_button')
        self.removeButton = DirectButton(parent=self.checkoutNode, relief=None, scale=1, pos=(-0.35, 0.0, -0.55),
                                         image=(model.find('**/QuitBtn_UP'), model.find('**/QuitBtn_DN'), model.find('**/QuitBtn_RLVR')),
                                         image_scale=(1.25, 1, 1), text=TTLocalizer.PizzaRemoveCart, text_scale=0.05,
                                         text_pos=TTLocalizer.DSDcancelPos, command=self.removeItem)
        self.placeOrderButton = DirectButton(parent=self.checkoutNode, relief=None, scale=1, pos=(0.45, 0.0, -0.65),
                                             image=(model.find('**/QuitBtn_UP'), model.find('**/QuitBtn_DN'), model.find('**/QuitBtn_RLVR')),
                                             image_scale=(1.25, 1, 1), text=TTLocalizer.PizzaPlaceOrder, text_scale=0.05,
                                             text_pos=TTLocalizer.DSDcancelPos, command=self.placeOrder)
        model.removeNode()

        # The list of items in our cart
        model = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.cartList = DirectScrolledList(parent=self.checkoutNode, relief=None, forceHeight=0.07, pos=(0.45, 0, -0.05),
                                           incButton_image=(model.find('**/FndsLst_ScrollUp'),
                                                            model.find('**/FndsLst_ScrollDN'),
                                                            model.find('**/FndsLst_ScrollUp_Rllvr'),
                                                            model.find('**/FndsLst_ScrollUp')), incButton_relief=None,
                                           incButton_scale=(1.3, 1.3, -1.3), incButton_pos=(0.0, 0, -0.5),
                                           incButton_image3_color=Vec4(1, 1, 1, 0.2),
                                           decButton_image=(model.find('**/FndsLst_ScrollUp'),
                                                            model.find('**/FndsLst_ScrollDN'),
                                                            model.find('**/FndsLst_ScrollUp_Rllvr'),
                                                            model.find('**/FndsLst_ScrollUp')), decButton_relief=None,
                                           decButton_scale=(1.3, 1.3, 1.3), decButton_pos=(0.0, 0, 0.47),
                                           decButton_image3_color=Vec4(1, 1, 1, 0.2), itemFrame_pos=(-0.237, 0, 0.41),
                                           itemFrame_scale=1.0, itemFrame_relief=DGG.SUNKEN,
                                           itemFrame_frameSize=(-0.05, 0.56, -0.87, 0.02), itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                           itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=12,
                                           items=[])
        model.removeNode()

        # This label shows product information
        self.cartProductLabel = DirectLabel(parent=self.checkoutNode, relief=None, pos=(-0.35, 0.0, -0.1), scale=0.075, text='',
                                            text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=12)

        # This label shows our totals
        self.totalsLabel = DirectLabel(parent=self.checkoutNode, relief=None, pos=(-0.60, 0.0, 0.3), scale=0.0675, text=TTLocalizer.PizzaTotals,
                                       text_font=ToontownGlobals.getInterfaceFont(), text_align=TextNode.ALeft)

        # Hide the interface because we're only loading it, not entering it
        self.hide()

        # Exit the interface if we get caged
        # Temp commented out because it activates self.exit automatically as soon as you enter the menu
        #self.accept('toon-caged', self.exit)

    def selectOption(self, index):
        if index == BUTTON_CLOSE:
            # Exit the interface
            self.exit()
        elif index == BUTTON_ADDRESS:
            # End the deal generation cycle
            taskMgr.remove(self.uniqueName('generateDeal'))

            # Open information interface
            self.requestInformation()
        elif index == BUTTON_BROWSE:
            # End the deal generation cycle
            taskMgr.remove(self.uniqueName('generateDeal'))

            # Open the ordering menu
            self.openMenu()

    def selectDeal(self, code):
        print("Selecting deal with code: {}".format(code))

    def generateDeal(self):
        # Update the deal code and description
        if self.activeDeals:
            deal = random.choice(self.activeDeals)

            code = deal[DEAL_CODE]
            self.dealButton['extraArgs'] = [code]

            desc = deal[DEAL_DESC]
            self.dealButton.setText(desc)

        # Get bounds of the new text and set it's position based on it
        deal = self.dealButton.component('text0')
        bMin, bMax = deal.getTightBounds()
        bound = bMax.x / 5
        self.dealButton.setPos(Point3(bound, 0.0, -0.65))

        # Make an interval that moves the text along the screen
        duration = bound * 5
        ival = LerpPosInterval(self.dealButton, duration, Point3(-bound, 0.0, -0.65))
        ival.start()

        # Show another deal after this one
        taskMgr.doMethodLater(duration + 0.25, self.generateDeal, self.uniqueName('generateDeal'), extraArgs=[])

    def enter(self):
        # Only allow us to enter the menu if we aren't already in it
        if self.isEntered == 1:
            return
        self.isEntered = 1

        # Lock the Toon down
        # TODO: (remove this if you are porting to a non-ttoff source)
        base.localAvatar.setLocked(True)

        # If we haven't loaded yet for some reason, load the interface
        if self.isLoaded == 0:
            self.load()

        # Darken the background
        base.transitions.fadeScreen(0.5)

        # Play a little song to go with the menu
        base.playMusic(self.music, looping=1)

        # Prompt the user to enter their information
        self.requestInformation()

        # Show the interface
        self.show()

    def requestInformation(self, retry=False):
        # We want to show the info screen and hide all others
        self.infoNode.show()
        self.titleNode.hide()
        self.menuNode.hide()
        self.checkoutNode.hide()

        # Adjust the UI to fit this screen
        self.logo.setPos(-0.35, 0.0, 0.0)
        self.infoLabel.setPos(-0.35, 0.0, -0.55)

        # Update our entry titles to match what info we want
        if self.infoState == STAGE_NAME:
            entryNames = TTLocalizer.PizzaEntryName
            labelText = TTLocalizer.PizzaInfoNameEntry
        elif self.infoState == STAGE_ADDRESS:
            entryNames = TTLocalizer.PizzaEntryAddress
            labelText = TTLocalizer.PizzaInfoAddressEntry
        elif self.infoState == STAGE_CARD:
            entryNames = TTLocalizer.PizzaEntryCard
            labelText = TTLocalizer.PizzaInfoCardEntry
        else:
            raise Exception('requestInformation - Invalid Info State: {}!'.format(self.infoState))

        if not retry:
            self.infoLabel.setText(labelText)
        else:
            self.failureSfx.play()

        # Update the entry labels and clear all entires
        for x in range(len(entryNames)):
            text = entryNames[x]
            label = self.entryLabels[x]
            label.setText(text)
            entry = self.entryInputs[x]
            entry.set('')

    def submitInformation(self):
        # Hide the information entry and show the main menu
        self.infoNode.hide()
        self.titleNode.show()

        # Advance to the next info state
        self.infoState += 1

        # Determine what to do next based on our info state
        # We just submitted our name info, so wrap it up into a customer object for later us
        # After that we just request information again for the address stage
        if self.infoState == STAGE_ADDRESS:
            # Iterate over our entries to gather the info
            information = []
            for entry in self.entryInputs:
                info = entry.get()
                information.append(info)
            first, last, email, phone = information
            # Make sure everything is filled out, otherwise tell the user to retry
            retry = False
            if first and last and email and phone:
                self.customer = Customer(first, last, email, phone)
                self.successSfx.play()
            else:
                self.infoLabel.setText(TTLocalizer.PizzaInfoIncorrectEntry)
                self.infoState -= 1
                retry = True
            # Now we want our address info
            self.requestInformation(retry)
        # This is for when we've submitted our address info, and we have to wrap it up as well
        # After this, we request one more time for our credit card info
        elif self.infoState == STAGE_CARD:
            # Iterate over our entries to gather the info
            information = []
            for entry in self.entryInputs:
                info = entry.get()
                information.append(info)
            street, city, state, zip = information
            # Make sure everything is filled out, otherwise tell the user to retry
            retry = False
            if street and city and state and zip:
                self.address = Address(street, city, state, zip)
                self.store = self.address.closest_store()
                self.menu = self.store.get_menu()
                self.successSfx.play()
            else:
                self.infoLabel.setText(TTLocalizer.PizzaInfoIncorrectEntry)
                self.infoState -= 1
                retry = True
            # Now we want our card info
            self.requestInformation(retry)
        # We now have the credit card info and are in the final state
        # Pack that up, and proceed to enter the title screen
        elif self.infoState == STAGE_FINAL:
            # Iterate over our entries to gather the info
            information = []
            for entry in self.entryInputs:
                info = entry.get()
                information.append(info)
            number, expire, security, zip = information
            # TODO: Add card checks from Anesidora
            if number and expire and security and zip:
                self.card = PaymentObject(number, expire, security, zip)
                self.successSfx.play()
            else:
                self.infoLabel.setText(TTLocalizer.PizzaInfoIncorrectEntry)
                self.infoState -= 1
                self.requestInformation(True)
                return

            # Set proper logo position
            self.logo.setPos(-0.5, 0, 0)

            # Update info label
            self.infoLabel.setText(TTLocalizer.PizzaCouponTitle)
            self.infoLabel.setPos(0.0, 0.0, -0.55)

            # Gather all coupon descriptions
            for deal in self.menu.coupons:
                # Get our deal info
                code = deal.code
                desc = deal.name

                # Make sure we don't include any carryout deals
                if 'carryout' not in desc:
                    self.activeDeals.append((code, desc))

            # Begin the deal generation cycle
            self.generateDeal()

            # Reset our info state to the beginning
            self.infoState = STAGE_NAME
        else:
            raise Exception('submitInformation - Invalid Info State: {}!'.format(self.infoState))

    def openMenu(self):
        # Hide title screen, show menu
        self.titleNode.hide()
        self.menuNode.show()

        # Adjust the UI to fit this screen
        self.logo.hide()
        self.infoLabel.setText(TTLocalizer.PizzaInfoSearch)
        self.infoLabel.setPos(-0.35, 0.0, 0.3)

    def closeMenu(self):
        # Hide the menu and show the title screen
        self.menuNode.hide()
        self.titleNode.show()

        # Set proper logo position
        self.logo.show()

        # Update info label
        self.infoLabel.setText(TTLocalizer.PizzaCouponTitle)
        self.infoLabel.setPos(0.0, 0.0, -0.55)

        # Begin the deal generation cycle
        self.generateDeal()

    def menuSearch(self, *args):
        # Clear out any previous products from our list
        self.menuList.removeAndDestroyAllItems()

        # Get the text in our entry box
        term = self.menuEntryInput.get()

        # Search the menu for items using this term
        items = self.menu.get(Name=term)

        # Iterate over all the items and create buttons for them to add to the list
        for item in items:
            # Get the product name but cut it off so it doesn't extend past our list
            name = item[ITEM_NAME]
            shortName = name[0:38]
            if len(shortName) < len(name):
                shortName += '...'
            product = DirectButton(parent=self.menuNode, relief=None, text=shortName, text_align=TextNode.ALeft,
                                   text_pos=(-0.025, -0.04, 0.0), text_scale=0.03, text1_bg=Vec4(0.5, 0.9, 1, 1),
                                   text2_bg=Vec4(1, 1, 0, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1), textMayChange=0,
                                   command=self.targetItem, extraArgs=[item])
            self.menuList.addItem(product, refresh=0)
        self.menuList.refresh()

    def targetItem(self, item):
        # Grab our product info
        name = item[ITEM_NAME]
        price = item[ITEM_PRICE]

        # Set the selected product ID
        self.productId = item

        # Make a string we can use for our product label
        text = name + '\n\n$' + price

        # Yeah... I'm lazy
        self.productLabel.setText(text)
        self.cartProductLabel.setText(text)

    def selectItem(self):
        if self.productId:
            self.cart.append(self.productId)
            self.purchaseSfx.play()

    def checkout(self):
        # Hide the menu, show the checkout, and hide the info label
        self.menuNode.hide()
        self.checkoutNode.show()
        self.infoLabel.hide()

        # Clear previous values
        self.productId = None
        self.cartProductLabel.setText('')

        # Clear out any previous products from our list
        self.cartList.removeAndDestroyAllItems()

        # This is a fake order that we only use to determine the price
        order = Order(self.store, self.customer, self.address)

        # Iterate over all the items and create buttons for them to add to the list
        for item in self.cart:
            # Get the product name but cut it off so it doesn't extend past our list
            name = item[ITEM_NAME]
            code = item[ITEM_CODE]
            shortName = name[0:38]
            if len(shortName) < len(name):
                shortName += '...'
            product = DirectButton(parent=self.menuNode, relief=None, text=shortName, text_align=TextNode.ALeft,
                                   text_pos=(-0.025, -0.04, 0.0), text_scale=0.03, text1_bg=Vec4(0.5, 0.9, 1, 1),
                                   text2_bg=Vec4(1, 1, 0, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1), textMayChange=0,
                                   command=self.targetItem, extraArgs=[item])
            self.cartList.addItem(product, refresh=0)
            order.add_item(code)
        self.cartList.refresh()

        # Make sure the order is valid though, or else throw an exception
        if self.cart:
            result = order.validate()
            if not result:
                raise Exception("checkout - Invalid Order!")

        # Get price info
        if self.cart:
            price = order.price()
            info = price['Order']
            breakdown = info['AmountsBreakdown']

            subtotal = breakdown['FoodAndBeverage']
            delivery = breakdown['DeliveryFee']
            tax = breakdown['Tax']
            total = breakdown['Customer']
        else:
            subtotal = 0
            delivery = 0
            tax = 0
            total = 0

        # Delete the temporary order
        del order

        text = TTLocalizer.PizzaTotals.format(subtotal, delivery, tax, total)
        self.totalsLabel.setText(text)

    def returnToCheckout(self):
        # Hide the checkout, show the menu, and show the info label
        self.checkoutNode.hide()
        self.menuNode.show()
        self.infoLabel.show()

        # Clear previous values
        self.productId = None
        self.productLabel.setText('')

    def removeItem(self):
        if self.productId and self.productId in self.cart:
            self.cart.remove(self.productId)
            self.checkout()
            self.cartProductLabel.setText('')
            self.successSfx.play()

    def placeOrder(self):
        if not self.cart:
            # TODO: Add error message here
            return

        # Create our order
        order = Order(self.store, self.customer, self.address)

        # Iterate over all the items in the cart and add them
        for item in self.cart:
            code = item[ITEM_CODE]
            order.add_item(code)

        # Make sure the order is valid, or else throw an exception
        result = order.validate()
        if not result:
            raise Exception("placeOrder - Invalid Order!")

        price = order.price()
        info = price['Order']
        breakdown = info['AmountsBreakdown']
        subtotal = breakdown['FoodAndBeverage']
        total = breakdown['Customer']

        if float(subtotal) < 10.0:
            raise Exception("placeOrder - Subtotal must be at least 10")

        result = order.place(self.card)
        print("Order placed with result: {}".format(result))

        text = TTLocalizer.PizzaOrderPlaced.format(total)
        # TODO: this will not work in a non-ttoff source
        base.localAvatar.setSystemMessage(0, text, whisperType=WhisperPopup.WTAnnouncement)

        fanfare = Sequence(Fanfare.makeFanfare(0, base.localAvatar)[0])
        fanfare.start()

        self.exit()

    def exit(self):
        # We can only exit the interface if we are currently in it
        if self.isEntered == 0:
            return
        self.isEntered = 0

        # End the deal generation cycle
        taskMgr.remove(self.uniqueName('generateDeal'))

        # Stop the music
        self.music.stop()

        # Remove the darkened screen effect
        base.transitions.noTransitions()

        # Ignore all messages
        self.ignoreAll()

        # Hide the interface
        self.hide()

        # Unlock the Toon
        # TODO: (remove this if you are porting to a non-ttoff source)
        base.localAvatar.setLocked(False)

    def toggleEntryFocus(self, state):
        # TODO: this may not work good in a non-ttoff source
        if state:
            localAvatar.chatMgr.setBackgroundFocus(False, True)
            base.localAvatar.disableAvatarControls()
        else:
            localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
            base.localAvatar.enableAvatarControls()
