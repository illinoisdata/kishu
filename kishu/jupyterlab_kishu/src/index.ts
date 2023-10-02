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


interface CommitSummary {
    commit_id: string;
    parent_id: string;
    message: string;
    timestamp: string;
    code_block?: string;
    runtime_ms?: number;
  }

interface LogAllResult {
    commit_graph: CommitSummary[];
}

interface CheckoutResult {
    status: string;
    message: string;
}

function commitSummaryToString(commit: CommitSummary): string {
  return `[${commit.commit_id}] ${commit.message}`;
}

function extractHashFromString(inputString: string): string | undefined {
  const regex = /\[([a-fA-F0-9-]+)\]\s/;
  const match = inputString.match(regex);
  if (match && match[1]) {
    return match[1];
  }
  return undefined;
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
      execute: async (_args) => {
        // TODO: Detect currently viewed notebook path.
        const notebook_id = (
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

        // List all commits.
        const log_all_result = await requestAPI<LogAllResult>('log_all', {
          method: 'POST',
          body: JSON.stringify({notebook_id: notebook_id}),
        });

        // Ask for the target commit ID.
        let commit_id = undefined;
        if (!log_all_result || log_all_result.commit_graph.length == 0) {
          // Failed to list, asking in text dialog directly.
          commit_id = (
            await InputDialog.getText({
              placeholder: '<commit_id>',
              title: trans.__('Checkout to...'),
              okLabel: trans.__('Checkout')
            })
          ).value ?? undefined;
        } else {
          // Show the list and ask to pick one item
          const selected_commit_str = (
            await InputDialog.getItem({
              items: log_all_result.commit_graph.map(commitSummaryToString),
              current: log_all_result.commit_graph.length - 1,
              editable: false,
              title: trans.__('Checkout to...'),
              okLabel: trans.__('Checkout')
            })
          ).value ?? undefined;
          if (selected_commit_str !== undefined) {
            console.log(`Selected selected_commit_str= ${selected_commit_str}`);
            commit_id = extractHashFromString(selected_commit_str);
          }
        }
        if (!commit_id) {
          window.alert(trans.__(`Kishu checkout requires commit ID.`));
          return;
        }
        console.log(`Selected commit_id= ${commit_id}`);

        // Make checkout request
        const checkout_result = await requestAPI<CheckoutResult>('checkout', {
          method: 'POST',
          body: JSON.stringify({notebook_id: notebook_id, commit_id: commit_id}),
        });

        // Report.
        if (checkout_result.status != 'ok') {
          window.alert(trans.__(`Kishu checkout failed: "${checkout_result.message}"`));
        } else {
          window.alert(trans.__(`Kishu checkout to ${commit_id} succeeded.\nPlease refresh this page.`));
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
