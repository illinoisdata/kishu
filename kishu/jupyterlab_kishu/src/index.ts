import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  ICommandPalette,
  InputDialog,
} from '@jupyterlab/apputils';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ITranslator } from '@jupyterlab/translation';

import { requestAPI } from './handler';

namespace CommandIDs {
  /**
   * Checkout a commit on the currently viewed file.
   */
  export const checkout = 'kishu:checkout';
}

interface CheckoutResult {
    status: string,
    message: string,
}

/**
 * Initialization data for the jupyterlab_kishu extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_kishu:plugin',
  description: 'Jupyter extension to interact with Kishu',
  autoStart: true,
  requires: [ICommandPalette, ITranslator],
  optional: [ISettingRegistry],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    translator: ITranslator,
    settingRegistry: ISettingRegistry | null,
  ) => {
    const { commands } = app;
    const trans = translator.load('jupyterlab');

    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then(settings => {
          console.log('jupyterlab_kishu settings loaded:', settings.composite);
        })
        .catch(reason => {
          console.error('Failed to load settings for jupyterlab_kishu.', reason);
        });
    }

    /**
     * Checkout
     */

    commands.addCommand(CommandIDs.checkout, {
      label: trans.__('Kishu: Checkout...'),
      execute: async (args: any) => {
        // Ask for inputs.
        let notebook_id = (
          await InputDialog.getText({
            placeholder: '<notebook_id>',
            title: trans.__('Checkout...'),
            okLabel: trans.__('Next')
          })
        ).value ?? undefined;
        if (!notebook_id) {
          window.alert(trans.__(`Kishu checkout requires notebook ID.`));
          return;
        }
        let commit_id = (
          await InputDialog.getText({
            placeholder: '<commit_id>',
            title: trans.__('Checkout to...'),
            okLabel: trans.__('Checkout')
          })
        ).value ?? undefined;
        if (!commit_id) {
          window.alert(trans.__(`Kishu checkout requires commit ID.`));
          return;
        }

        // Make checkout request
        let checkout_result = await requestAPI<CheckoutResult>('checkout', {
          method: 'POST',
          body: JSON.stringify({
            notebook_id: notebook_id,
            commit_id: commit_id,
          }),
        });

        // Report.
        if (checkout_result.status != 'ok') {
          window.alert(trans.__(`Kishu checkout failed: "${checkout_result.message}"`));
        } else {
          window.alert(trans.__(`Kishu checkout to ${commit_id} succeeded. Please refresh this page.`));
        }
      }
    });
    palette.addItem({
      command: CommandIDs.checkout,
      category: 'Kishu',
    });
  }
};

export default plugin;
