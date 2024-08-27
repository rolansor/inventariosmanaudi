/**
 * @license Copyright (c) 2003-2024, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see LICENSE.md or https://ckeditor.com/legal/ckeditor-oss-license
 */
/**
 * @module ckbox/ckboxui
 */
import { icons, Plugin } from 'ckeditor5/src/core.js';
import { ButtonView } from 'ckeditor5/src/ui.js';
/**
 * The CKBoxUI plugin. It introduces the `'ckbox'` toolbar button.
 */
export default class CKBoxUI extends Plugin {
    /**
     * @inheritDoc
     */
    static get pluginName() {
        return 'CKBoxUI';
    }
    /**
     * @inheritDoc
     */
    afterInit() {
        const editor = this.editor;
        // Do not register the `ckbox` button if the command does not exist.
        // This might happen when CKBox library is not loaded on the page.
        if (!editor.commands.get('ckbox')) {
            return;
        }
        const t = editor.t;
        const componentFactory = editor.ui.componentFactory;
        componentFactory.add('ckbox', locale => {
            const command = editor.commands.get('ckbox');
            const button = new ButtonView(locale);
            button.set({
                label: t('Open file manager'),
                icon: icons.browseFiles,
                tooltip: true
            });
            button.bind('isOn', 'isEnabled').to(command, 'value', 'isEnabled');
            button.on('execute', () => {
                editor.execute('ckbox');
            });
            return button;
        });
        if (editor.plugins.has('ImageInsertUI')) {
            const imageInsertUI = editor.plugins.get('ImageInsertUI');
            imageInsertUI.registerIntegration({
                name: 'assetManager',
                observable: () => editor.commands.get('ckbox'),
                buttonViewCreator: () => {
                    const button = this.editor.ui.componentFactory.create('ckbox');
                    button.icon = icons.imageAssetManager;
                    button.bind('label').to(imageInsertUI, 'isImageSelected', isImageSelected => isImageSelected ?
                        t('Replace image with file manager') :
                        t('Insert image with file manager'));
                    return button;
                },
                formViewCreator: () => {
                    const button = this.editor.ui.componentFactory.create('ckbox');
                    button.icon = icons.imageAssetManager;
                    button.withText = true;
                    button.bind('label').to(imageInsertUI, 'isImageSelected', isImageSelected => isImageSelected ?
                        t('Replace with file manager') :
                        t('Insert with file manager'));
                    button.on('execute', () => {
                        imageInsertUI.dropdownView.isOpen = false;
                    });
                    return button;
                }
            });
        }
    }
}
